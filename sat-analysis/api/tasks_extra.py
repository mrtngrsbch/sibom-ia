"""
Background tasks para análisis Sentinel-1 y MODIS.

Se integra con el TaskStore definido en tasks.py.
"""
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import matplotlib  # type: ignore[import-untyped]
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # type: ignore[import-untyped]  # noqa: E402
import numpy as np

from sat_analysis.services import (
    ArbaService,
    ModisError,
    ModisService,
    PartidaParser,
    Sentinel1Error,
    Sentinel1Service,
    StacService,
)
from sat_analysis.services.arba import ArbaError
from sat_analysis.services.stac import get_pixel_area_m2

from .models import AnalyzeResponse, ImageUrls, TaskStatus

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Sentinel-1
# ─────────────────────────────────────────────────────────────────────────────


async def run_s1_analysis_task(
    task_id: str,
    partida: str,
    codigo_partido: str,
    years: int,
    samples_per_year: int,
    output_dir: Path,
) -> None:
    """
    Ejecuta análisis Sentinel-1 SAR en background.

    Args:
        task_id: ID único de la tarea
        partida: Número de partida individual (ej: "4606")
        codigo_partido: Código de partido ARBA (ej: "002")
        years: Años de histórico
        samples_per_year: Imágenes por año
        output_dir: Directorio para guardar imágenes
    """
    # Importar aquí para evitar circular import
    from .tasks import task_store

    try:
        await task_store.update_progress(
            task_id, 0.0, "Iniciando análisis Sentinel-1 SAR…", TaskStatus.PROCESSING
        )

        # 1. Parsear partida
        try:
            parser = PartidaParser()
            partida_arba = parser.parse(f"{codigo_partido}{partida.zfill(6)}")
        except ValueError as exc:
            await task_store.update_progress(task_id, 0.0, f"Error en partida: {exc}", TaskStatus.FAILED)
            _set_error(await task_store.get(task_id), str(exc))
            return

        await task_store.update_progress(
            task_id, 0.05, f"Consultando parcela {partida_arba.formato_completo}…"
        )

        # 2. Geometría ARBA
        try:
            arba = ArbaService()
            parcel = arba.get_parcel_geometry(partida_arba)
            if parcel is None:
                msg = f"Partida {partida_arba.formato_completo} no encontrada en ARBA"
                await task_store.update_progress(task_id, 0.0, msg, TaskStatus.FAILED)
                _set_error(await task_store.get(task_id), msg)
                return
            parcel_bbox = parcel.bbox
            parcel_geometry = parcel.geometry
        except ArbaError as exc:
            msg = f"Error consultando ARBA: {exc}"
            await task_store.update_progress(task_id, 0.0, msg, TaskStatus.FAILED)
            _set_error(await task_store.get(task_id), msg)
            return

        await task_store.update_progress(task_id, 0.1, "Buscando imágenes Sentinel-1…")

        # 3. Buscar imágenes
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        date_range = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"

        s1 = Sentinel1Service()
        try:
            items = s1.search_sampled(
                bbox=parcel_bbox,
                date_range=date_range,
                samples_per_year=samples_per_year,
                start_date=start_date,
                end_date=end_date,
            )
        except Sentinel1Error as exc:
            msg = f"Error buscando imágenes SAR: {exc}"
            await task_store.update_progress(task_id, 0.0, msg, TaskStatus.FAILED)
            _set_error(await task_store.get(task_id), msg)
            return

        if not items:
            msg = "No se encontraron imágenes Sentinel-1 para el período"
            await task_store.update_progress(task_id, 0.0, msg, TaskStatus.FAILED)
            _set_error(await task_store.get(task_id), msg)
            return

        await task_store.update_progress(task_id, 0.2, f"Encontradas {len(items)} imágenes SAR")

        # Actualizar total_images
        response = await task_store.get(task_id)
        if response:
            response.total_images = len(items)

        # 4. Procesar imágenes
        results_dto = []
        total = len(items)
        partida_clean = partida.replace("coords:", "c").replace(":", "_")

        for i, item in enumerate(items):
            progress_val = 0.25 + 0.7 * ((i + 1) / total)
            await task_store.update_progress(
                task_id,
                progress_val,
                f"Procesando imagen SAR {i + 1}/{total}…",
            )

            try:
                bands = s1.download_bands(item, bbox=parcel_bbox)
                pixel_area = float(get_pixel_area_m2(bands.transform, bands.crs))
                areas = s1.compute_water_areas(bands, pixel_area)
                date_str = item.datetime[:10].replace("-", "")

                # Crear máscara de la parcela para dibujar el recuadro
                stac_svc = StacService()
                parcel_mask = stac_svc.create_parcel_mask(
                    shape=bands.vv.shape,
                    geometry=parcel_geometry,
                    bbox=parcel_bbox,
                    image_crs=bands.crs,
                    transform=bands.transform,
                ) if parcel_geometry is not None else None

                img_urls = _save_s1_visualizations(
                    bands=bands,
                    partida_clean=partida_clean,
                    date_str=date_str,
                    output_dir=output_dir,
                    water_threshold_vv=Sentinel1Service.WATER_VV_THRESHOLD,
                    parcel_mask=parcel_mask,
                    parcel_bbox=parcel_bbox,
                )

                # Reutilizar ImageResultDTO: water_ha = agua SAR, wetland_ha = suelo húmedo
                from .models import ImageResultDTO
                results_dto.append(
                    ImageResultDTO(
                        date=item.datetime,
                        water_ha=areas["water_ha"],
                        wetland_ha=areas["moist_ha"],
                        vegetation_ha=0.0,
                        other_ha=areas["dry_ha"],
                        cloud_cover=None,
                        images=img_urls,
                    )
                )
            except Exception as exc:
                logger.warning("Error procesando imagen SAR %d: %s", i, exc)
                continue

        if not results_dto:
            msg = "Error procesando todas las imágenes SAR"
            await task_store.update_progress(task_id, 0.0, msg, TaskStatus.FAILED)
            _set_error(await task_store.get(task_id), msg)
            return

        # 5. Finalizar
        response = await task_store.get(task_id)
        if response:
            response.status = TaskStatus.COMPLETED
            response.progress = 1.0
            response.message = f"Análisis SAR completado: {len(results_dto)} imágenes procesadas"
            response.results = results_dto
            response.total_images = len(results_dto)

        await task_store.update_progress(
            task_id, 1.0,
            f"Análisis SAR completado: {len(results_dto)} imágenes",
            TaskStatus.COMPLETED,
        )

    except Exception as exc:
        logger.exception("Error inesperado en análisis SAR: %s", exc)
        await task_store.update_progress(
            task_id, 0.0, f"Error inesperado: {exc}", TaskStatus.FAILED
        )
        _set_error(await task_store.get(task_id), str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# MODIS
# ─────────────────────────────────────────────────────────────────────────────


async def run_modis_analysis_task(
    task_id: str,
    partida: str,
    codigo_partido: str,
    years: int,
    samples_per_year: int,
    output_dir: Path,
) -> None:
    """
    Ejecuta análisis MODIS en background.

    Args:
        task_id: ID único de la tarea
        partida: Número de partida individual (ej: "4606")
        codigo_partido: Código de partido ARBA (ej: "002")
        years: Años de histórico
        samples_per_year: Imágenes por año
        output_dir: Directorio para guardar imágenes
    """
    from .tasks import task_store

    try:
        await task_store.update_progress(
            task_id, 0.0, "Iniciando análisis MODIS…", TaskStatus.PROCESSING
        )

        # 1. Parsear partida
        try:
            parser = PartidaParser()
            partida_arba = parser.parse(f"{codigo_partido}{partida.zfill(6)}")
        except ValueError as exc:
            await task_store.update_progress(task_id, 0.0, f"Error en partida: {exc}", TaskStatus.FAILED)
            _set_error(await task_store.get(task_id), str(exc))
            return

        await task_store.update_progress(
            task_id, 0.05, f"Consultando parcela {partida_arba.formato_completo}…"
        )

        # 2. Geometría ARBA
        try:
            arba = ArbaService()
            parcel = arba.get_parcel_geometry(partida_arba)
            if parcel is None:
                msg = f"Partida {partida_arba.formato_completo} no encontrada en ARBA"
                await task_store.update_progress(task_id, 0.0, msg, TaskStatus.FAILED)
                _set_error(await task_store.get(task_id), msg)
                return
            parcel_bbox = parcel.bbox
            parcel_geometry = parcel.geometry
        except ArbaError as exc:
            msg = f"Error consultando ARBA: {exc}"
            await task_store.update_progress(task_id, 0.0, msg, TaskStatus.FAILED)
            _set_error(await task_store.get(task_id), msg)
            return

        await task_store.update_progress(task_id, 0.1, "Buscando imágenes MODIS…")

        # 3. Buscar imágenes
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        date_range = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"

        modis = ModisService()
        try:
            items = modis.search_sampled(
                bbox=parcel_bbox,
                date_range=date_range,
                samples_per_year=samples_per_year,
                start_date=start_date,
                end_date=end_date,
            )
        except ModisError as exc:
            msg = f"Error buscando imágenes MODIS: {exc}"
            await task_store.update_progress(task_id, 0.0, msg, TaskStatus.FAILED)
            _set_error(await task_store.get(task_id), msg)
            return

        if not items:
            msg = "No se encontraron imágenes MODIS para el período"
            await task_store.update_progress(task_id, 0.0, msg, TaskStatus.FAILED)
            _set_error(await task_store.get(task_id), msg)
            return

        await task_store.update_progress(task_id, 0.2, f"Encontradas {len(items)} imágenes MODIS")

        response = await task_store.get(task_id)
        if response:
            response.total_images = len(items)

        # 4. Procesar imágenes
        results_dto = []
        total = len(items)
        partida_clean = partida.replace("coords:", "c").replace(":", "_")

        for i, item in enumerate(items):
            progress_val = 0.25 + 0.7 * ((i + 1) / total)
            await task_store.update_progress(
                task_id,
                progress_val,
                f"Procesando imagen MODIS {i + 1}/{total}…",
            )

            try:
                bands = modis.download_bands(item, bbox=parcel_bbox)
                indices = ModisService.compute_indices(bands)
                date_str = item.datetime[:10].replace("-", "")

                # Estimar áreas con NDWI > 0 como agua, NDVI > 0.3 como vegetación
                pixel_area = float(get_pixel_area_m2(bands.transform, bands.crs))
                water_mask = indices["ndwi"] > 0.1
                veg_mask = ~water_mask & (indices["ndvi"] > 0.3)
                other_mask = ~water_mask & ~veg_mask

                def _ha(mask: np.ndarray) -> float:
                    return round(float(np.sum(mask) * pixel_area / 10000), 2)

                # Crear máscara de la parcela para dibujar el recuadro
                stac_svc = StacService()
                parcel_mask = stac_svc.create_parcel_mask(
                    shape=bands.red.shape,
                    geometry=parcel_geometry,
                    bbox=parcel_bbox,
                    image_crs=bands.crs,
                    transform=bands.transform,
                ) if parcel_geometry is not None else None

                img_urls = _save_modis_visualizations(
                    bands=bands,
                    indices=indices,
                    partida_clean=partida_clean,
                    date_str=date_str,
                    output_dir=output_dir,
                    parcel_mask=parcel_mask,
                    parcel_bbox=parcel_bbox,
                )

                from .models import ImageResultDTO
                results_dto.append(
                    ImageResultDTO(
                        date=item.datetime,
                        water_ha=_ha(water_mask),
                        wetland_ha=0.0,
                        vegetation_ha=_ha(veg_mask),
                        other_ha=_ha(other_mask),
                        cloud_cover=None,
                        images=img_urls,
                    )
                )
            except Exception as exc:
                logger.warning("Error procesando imagen MODIS %d: %s", i, exc)
                continue

        if not results_dto:
            msg = "Error procesando todas las imágenes MODIS"
            await task_store.update_progress(task_id, 0.0, msg, TaskStatus.FAILED)
            _set_error(await task_store.get(task_id), msg)
            return

        # 5. Finalizar
        response = await task_store.get(task_id)
        if response:
            response.status = TaskStatus.COMPLETED
            response.progress = 1.0
            response.message = f"Análisis MODIS completado: {len(results_dto)} imágenes"
            response.results = results_dto
            response.total_images = len(results_dto)

        await task_store.update_progress(
            task_id, 1.0,
            f"Análisis MODIS completado: {len(results_dto)} imágenes",
            TaskStatus.COMPLETED,
        )

    except Exception as exc:
        logger.exception("Error inesperado en análisis MODIS: %s", exc)
        await task_store.update_progress(
            task_id, 0.0, f"Error inesperado: {exc}", TaskStatus.FAILED
        )
        _set_error(await task_store.get(task_id), str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de visualización
# ─────────────────────────────────────────────────────────────────────────────


def _draw_parcel_contour(ax: Any, parcel_mask: "np.ndarray | None", color: str = "white") -> None:
    """Dibuja el contorno real de la parcela usando la máscara rasterizada.

    Usa ax.contour() sobre la máscara binaria, lo que reproduce la geometría
    exacta de la parcela. Funciona bien con sensores de alta resolución (10 m).
    """
    if parcel_mask is not None:
        ax.contour(
            parcel_mask.astype(float),
            levels=[0.5],
            colors=[color],
            linewidths=2.0,
            alpha=0.9,
        )


def _draw_parcel_outline(
    ax: Any,
    parcel_bbox: "list[float] | None",
    transform: Any,
    crs: Any,
    color: str = "white",
) -> None:
    """
    Dibuja el perímetro de la parcela proyectando el bbox WGS84
    al espacio de píxeles de la imagen.

    A diferencia de ax.contour() sobre la máscara rasterizada,
    este método produce bordes siempre limpios y rectos sin importar
    la resolución del sensor (MODIS 500 m incluido).
    """
    if parcel_bbox is None or transform is None or crs is None:
        return
    try:
        from pyproj import Transformer
        minx, miny, maxx, maxy = parcel_bbox
        try:
            img_epsg = crs.to_epsg()
            target_crs = f"EPSG:{img_epsg}" if img_epsg else crs
        except Exception:
            target_crs = crs
        transformer = Transformer.from_crs("EPSG:4326", target_crs, always_xy=True)
        corners = [(minx, miny), (minx, maxy), (maxx, maxy), (maxx, miny), (minx, miny)]
        inv_transform = ~transform
        cols, rows = [], []
        for lon, lat in corners:
            x, y = transformer.transform(lon, lat)
            col, row = inv_transform * (x, y)
            cols.append(col)
            rows.append(row)
        ax.plot(cols, rows, color=color, linewidth=2.0, alpha=0.9)
    except Exception as exc:
        logger.debug("No se pudo dibujar contorno de parcela: %s", exc)


def _save_s1_visualizations(
    bands: Any,
    partida_clean: str,
    date_str: str,
    output_dir: Path,
    water_threshold_vv: float = 0.05,
    parcel_mask: "np.ndarray | None" = None,
    parcel_bbox: "list[float] | None" = None,
) -> ImageUrls:
    """Genera y guarda visualizaciones SAR para una imagen Sentinel-1."""
    output_dir.mkdir(parents=True, exist_ok=True)
    urls = ImageUrls()

    vv: np.ndarray = bands.vv
    vh: np.ndarray = bands.vh

    # ── VV ───────────────────────────────────────────────────────────────────
    urls.sar_vv = _save_single_image(
        data=vv,
        cmap="gray",
        vmin=0,
        vmax=0.5,
        title=f"Sentinel-1 VV - {partida_clean} | {date_str}",
        filename=f"sar_vv_{partida_clean}_{date_str}.png",
        output_dir=output_dir,
        colorbar_label="Backscatter VV (linear)",
        parcel_mask=parcel_mask,
    )

    # ── VH ───────────────────────────────────────────────────────────────────
    if np.any(vh > 0):
        urls.sar_vh = _save_single_image(
            data=vh,
            cmap="gray",
            vmin=0,
            vmax=0.2,
            title=f"Sentinel-1 VH - {partida_clean} | {date_str}",
            filename=f"sar_vh_{partida_clean}_{date_str}.png",
            output_dir=output_dir,
            colorbar_label="Backscatter VH (linear)",
            parcel_mask=parcel_mask,
        )

    # ── SAR RGB (VV, VH, VV/VH) ──────────────────────────────────────────────
    try:
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.where(vh > 0, vv / vh, 0.0)

        def _stretch(arr: np.ndarray, lo: float, hi: float) -> np.ndarray:
            return np.clip((arr - lo) / (hi - lo + 1e-9), 0.0, 1.0).astype(np.float32)

        r = _stretch(vv, 0.0, 0.5)
        g = _stretch(vh, 0.0, 0.15)
        b = _stretch(ratio, 0.0, 5.0)
        rgb = np.stack([r, g, b], axis=-1)

        fig, ax = plt.subplots(figsize=(10, 8))
        ax.imshow(rgb)
        _draw_parcel_contour(ax, parcel_mask, color="white")
        ax.set_title(f"Sentinel-1 SAR RGB (VV/VH/ratio) - {partida_clean} | {date_str}",
                     fontsize=10, fontweight="bold")
        ax.axis("off")
        fname = f"sar_rgb_{partida_clean}_{date_str}.png"
        fpath = output_dir / fname
        plt.savefig(fpath, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        urls.sar_rgb = f"/images/{fname}"
    except Exception as exc:
        logger.warning("Error generando SAR RGB: %s", exc)

    # ── Water mask ────────────────────────────────────────────────────────────
    try:
        water_mask = vv < water_threshold_vv
        moist_mask = ~water_mask & (vv < 0.15)
        classification = np.where(water_mask, 1, np.where(moist_mask, 2, 0))

        from matplotlib.colors import ListedColormap
        cmap_sar = ListedColormap(["#BDBDBD", "#2196F3", "#8BC34A"])
        fig, ax = plt.subplots(figsize=(10, 8))
        im = ax.imshow(classification, cmap=cmap_sar, vmin=0, vmax=2)
        plt.colorbar(im, ax=ax, label="0=Seco | 1=Agua | 2=Húmedo", ticks=[0, 1, 2])
        _draw_parcel_contour(ax, parcel_mask, color="white")
        ax.set_title(f"Sentinel-1 Agua/Humedad - {partida_clean} | {date_str}",
                     fontsize=10, fontweight="bold")
        ax.axis("off")
        fname = f"sar_water_{partida_clean}_{date_str}.png"
        fpath = output_dir / fname
        plt.savefig(fpath, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        urls.sar_water = f"/images/{fname}"
    except Exception as exc:
        logger.warning("Error generando SAR water mask: %s", exc)

    return urls


def _save_modis_visualizations(
    bands: Any,
    indices: dict[str, np.ndarray],
    partida_clean: str,
    date_str: str,
    output_dir: Path,
    parcel_mask: "np.ndarray | None" = None,
    parcel_bbox: "list[float] | None" = None,
) -> ImageUrls:
    """Genera y guarda visualizaciones para una imagen MODIS."""
    output_dir.mkdir(parents=True, exist_ok=True)
    urls = ImageUrls()

    # ── MODIS RGB ─────────────────────────────────────────────────────────────
    try:
        def _norm(arr: np.ndarray) -> np.ndarray:
            p2, p98 = np.percentile(arr[arr > 0], [2, 98]) if np.any(arr > 0) else (0.0, 0.3)
            return np.clip((arr - p2) / (p98 - p2 + 1e-9), 0.0, 1.0).astype(np.float32)

        rgb = np.stack([_norm(bands.red), _norm(bands.green), _norm(bands.blue)], axis=-1)
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.imshow(rgb)
        _draw_parcel_outline(ax, parcel_bbox, bands.transform, bands.crs, color="white")
        ax.set_title(f"MODIS RGB 500 m - {partida_clean} | {date_str}", fontsize=10, fontweight="bold")
        ax.axis("off")
        fname = f"modis_rgb_{partida_clean}_{date_str}.png"
        plt.savefig(output_dir / fname, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        urls.modis_rgb = f"/images/{fname}"
    except Exception as exc:
        logger.warning("Error generando MODIS RGB: %s", exc)

    # ── NDVI MODIS ────────────────────────────────────────────────────────────
    urls.modis_ndvi = _save_single_image(
        data=indices["ndvi"],
        cmap=plt.cm.RdYlGn_r,  # type: ignore[attr-defined]
        vmin=-0.2,
        vmax=0.9,
        title=f"MODIS NDVI 500 m - {partida_clean} | {date_str}",
        filename=f"modis_ndvi_{partida_clean}_{date_str}.png",
        output_dir=output_dir,
        colorbar_label="NDVI",
        parcel_bbox=parcel_bbox,
        transform=bands.transform,
        crs=bands.crs,
    )

    # ── NDWI MODIS ────────────────────────────────────────────────────────────
    urls.modis_ndwi = _save_single_image(
        data=indices["ndwi"],
        cmap=plt.cm.RdYlBu_r,  # type: ignore[attr-defined]
        vmin=-0.5,
        vmax=0.5,
        title=f"MODIS NDWI 500 m - {partida_clean} | {date_str}",
        filename=f"modis_ndwi_{partida_clean}_{date_str}.png",
        output_dir=output_dir,
        colorbar_label="NDWI",
        parcel_bbox=parcel_bbox,
        transform=bands.transform,
        crs=bands.crs,
    )

    # ── EVI MODIS ─────────────────────────────────────────────────────────────
    urls.modis_evi = _save_single_image(
        data=indices["evi"],
        cmap=plt.cm.RdYlGn_r,  # type: ignore[attr-defined]
        vmin=-0.2,
        vmax=0.8,
        title=f"MODIS EVI 500 m - {partida_clean} | {date_str}",
        filename=f"modis_evi_{partida_clean}_{date_str}.png",
        output_dir=output_dir,
        colorbar_label="EVI",
        parcel_bbox=parcel_bbox,
        transform=bands.transform,
        crs=bands.crs,
    )

    return urls


def _save_single_image(
    data: np.ndarray,
    cmap: Any,
    vmin: float,
    vmax: float,
    title: str,
    filename: str,
    output_dir: Path,
    colorbar_label: str = "",
    parcel_mask: "np.ndarray | None" = None,
    parcel_bbox: "list[float] | None" = None,
    transform: Any = None,
    crs: Any = None,
) -> str | None:
    """Guarda un array como imagen PNG con colormap. Devuelve la URL relativa."""
    try:
        fig, ax = plt.subplots(figsize=(10, 8))
        im = ax.imshow(data, cmap=cmap, vmin=vmin, vmax=vmax)
        plt.colorbar(im, ax=ax, label=colorbar_label)
        # Usa contorno de máscara real (alta resolución) o bbox proyectado (baja resolución)
        if parcel_mask is not None:
            _draw_parcel_contour(ax, parcel_mask, color="white")
        else:
            _draw_parcel_outline(ax, parcel_bbox, transform, crs, color="white")
        ax.set_title(title, fontsize=10, fontweight="bold")
        ax.axis("off")
        fpath = output_dir / filename
        plt.savefig(fpath, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return f"/images/{filename}"
    except Exception as exc:
        logger.warning("Error guardando imagen %s: %s", filename, exc)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Utilidades internas
# ─────────────────────────────────────────────────────────────────────────────


def _set_error(response: AnalyzeResponse | None, msg: str) -> None:
    """Asigna error a la respuesta si existe."""
    if response is not None:
        response.error = msg
