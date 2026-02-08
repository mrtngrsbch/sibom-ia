'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Info, AlertTriangle, TrendingUp, TrendingDown, Minus, Satellite, Droplets, Leaf, Package } from '@/lib/icons';
import Link from 'next/link';

/**
 * Página de ayuda para el analizador satelital.
 *
 * Explica cómo funciona el sistema, qué métricas calcula,
 * y cómo interpretar los resultados.
 */
export default function AyudaSatelitePage() {
  return (
    <div className="container mx-auto p-6 max-w-6xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 bg-primary-600 rounded-xl flex items-center justify-center">
            <Satellite className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
              Ayuda - Análisis Satelital
            </h1>
            <p className="text-slate-600 dark:text-slate-400">
              Guía completa para interpretar los resultados del análisis de parcelas catastrales
            </p>
          </div>
        </div>
        <Button variant="outline" asChild>
          <Link href="/satelite">
            ← Volver al Análisis
          </Link>
        </Button>
      </div>

      {/* Tabla de contenidos */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            Tabla de Contenidos
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <h3 className="font-semibold text-slate-900 dark:text-white mb-2">¿Cómo funciona?</h3>
              <ul className="space-y-1 text-sm text-slate-600 dark:text-slate-400">
                <li>• Flujo del análisis</li>
                <li>• Búsqueda de imágenes STAC</li>
                <li>• Clasificación de píxeles</li>
                <li>• Cálculo de áreas</li>
              </ul>
            </div>
            <div className="space-y-2">
              <h3 className="font-semibold text-slate-900 dark:text-white mb-2">Métricas</h3>
              <ul className="space-y-1 text-sm text-slate-600 dark:text-slate-400">
                <li>• Áreas por clase (ha)</li>
                <li>• Porcentaje afectado</li>
                <li>• Tendencias</li>
                <li>• Picos de anegamiento</li>
              </ul>
            </div>
            <div className="space-y-2">
              <h3 className="font-semibold text-slate-900 dark:text-white mb-2">Índices</h3>
              <ul className="space-y-1 text-sm text-slate-600 dark:text-slate-400">
                <li>• NDWI (Agua)</li>
                <li>• NDVI (Vegetación)</li>
                <li>• NDMI (Humedad)</li>
                <li>• NDSI (Salinidad)</li>
              </ul>
            </div>
            <div className="space-y-2">
              <h3 className="font-semibold text-slate-900 dark:text-white mb-2">Preguntas</h3>
              <ul className="space-y-1 text-sm text-slate-600 dark:text-slate-400">
                <li>• ¿Más imágenes = mejor accuracy?</li>
                <li>• ¿Hace promedio?</li>
                <li>• ¿Es ponderado?</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Sección 1: ¿Cómo funciona? */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>¿Cómo funciona el análisis?</CardTitle>
          <CardDescription>
            El sistema utiliza imágenes Sentinel-2 para clasificar el uso de suelo en una parcela catastral
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <Info className="w-5 h-5 text-blue-600" />
              Flujo del análisis
            </h3>
            <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-4 space-y-3">
              <div className="flex items-start gap-3">
                <Badge variant="outline" className="mt-1">1</Badge>
                <div>
                  <p className="font-medium">Búsqueda de imágenes STAC</p>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    Busca imágenes Sentinel-2 L2A con muestreo temporal uniforme. Para 2 años con 4 imágenes/año, selecciona 8 imágenes distribuidas uniformemente.
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Badge variant="outline" className="mt-1">2</Badge>
                <div>
                  <p className="font-medium">Descarga de bandas espectrales</p>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    Descarga 6 bandas: B02 (Blue), B03 (Green), B04 (Red), B08 (NIR), B11 (SWIR1), B12 (SWIR2)
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Badge variant="outline" className="mt-1">3</Badge>
                <div>
                  <p className="font-medium">Cálculo de índices espectrales</p>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    Calcula NDWI, NDVI, NDMI, MNDWI, NDSI y Salinity Index para cada píxel
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Badge variant="outline" className="mt-1">4</Badge>
                <div>
                  <p className="font-medium">Clasificación de píxeles</p>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    Usa umbrales fijos para clasificar cada píxel en 4 categorías: Agua, Humedal, Vegetación, Otros
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Badge variant="outline" className="mt-1">5</Badge>
                <div>
                  <p className="font-medium">Cálculo de áreas</p>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    Cuenta píxeles de cada clase dentro de la parcela y convierte a hectáreas
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Badge variant="outline" className="mt-1">6</Badge>
                <div>
                  <p className="font-medium">Generación de visualizaciones</p>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    Crea imágenes RGB, de clasificación y de índices espectrales para cada fecha
                  </p>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Sección 2: Clasificación */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Leaf className="w-5 h-5 text-green-600" />
            Clasificación de Píxeles
          </CardTitle>
          <CardDescription>
            El sistema usa umbrales fijos para clasificar cada píxel en 4 categorías
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-8 h-8 rounded bg-blue-600 flex items-center justify-center">
                    <Droplets className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h4 className="font-bold text-blue-600">Agua</h4>
                    <Badge variant="outline" className="text-xs">Clase 1</Badge>
                  </div>
                </div>
                <div className="text-sm text-slate-600 dark:text-slate-400">
                  <p className="font-medium mb-1">Umbrales:</p>
                  <ul className="space-y-1">
                    <li>• NDWI mayor a 0.15 (agua abierta)</li>
                    <li>• MNDWI mayor a 0.25 (agua turbia)</li>
                  </ul>
                </div>
              </div>

              <div className="bg-green-900/10 dark:bg-green-900/20 border border-green-700 dark:border-green-800 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-8 h-8 rounded bg-green-800 flex items-center justify-center">
                    <Leaf className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h4 className="font-bold text-green-800">Humedal</h4>
                    <Badge variant="outline" className="text-xs">Clase 2</Badge>
                  </div>
                </div>
                <div className="text-sm text-slate-600 dark:text-slate-400">
                  <p className="font-medium mb-1">Umbrales:</p>
                  <ul className="space-y-1">
                    <li>• NDVI mayor a 0.35 (vegetación)</li>
                    <li>• NDMI mayor a 0.10 (humedad)</li>
                    <li>• NDWI mayor a -0.6 (algo de agua)</li>
                    <li>• NO agua (clase 1)</li>
                  </ul>
                </div>
              </div>

              <div className="bg-green-50 dark:bg-green-900/10 border border-green-200 dark:border-green-800 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-8 h-8 rounded bg-green-600 flex items-center justify-center">
                    <Leaf className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h4 className="font-bold text-green-600">Vegetación</h4>
                    <Badge variant="outline" className="text-xs">Clase 3</Badge>
                  </div>
                </div>
                <div className="text-sm text-slate-600 dark:text-slate-400">
                  <p className="font-medium mb-1">Umbrales:</p>
                  <ul className="space-y-1">
                    <li>• NDVI mayor a 0.5 (vegetación)</li>
                    <li>• NDMI menor a 0.2 (no es humedal)</li>
                    <li>• NO agua (clase 1)</li>
                    <li>• NO humedal (clase 2)</li>
                  </ul>
                </div>
              </div>

              <div className="bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-8 h-8 rounded bg-slate-500 flex items-center justify-center">
                    <Package className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-600">Otros</h4>
                    <Badge variant="outline" className="text-xs">Clase 0</Badge>
                  </div>
                </div>
                <div className="text-sm text-slate-600 dark:text-slate-400">
                  <p className="font-medium mb-1">Descripción:</p>
                  <ul className="space-y-1">
                    <li>• Suelo desnudo</li>
                    <li>• Construcciones</li>
                    <li>• Todo lo que no es agua, humedal o vegetación</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Sección 3: Índices espectrales */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Satellite className="w-5 h-5 text-purple-600" />
            Índices Espectrales
          </CardTitle>
          <CardDescription>
            Índices calculados desde las bandas Sentinel-2 para clasificar el uso de suelo
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-700">
                  <th className="text-left p-3 font-semibold">Índice</th>
                  <th className="text-left p-3 font-semibold">Fórmula</th>
                  <th className="text-left p-3 font-semibold">Rango</th>
                  <th className="text-left p-3 font-semibold">Uso</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-slate-100 dark:border-slate-800">
                  <td className="p-3 font-medium text-blue-600">NDWI</td>
                  <td className="p-3 font-mono text-xs">(Green - NIR) / (Green + NIR)</td>
                  <td className="p-3">-1 a 1</td>
                  <td className="p-3">Detección de agua</td>
                </tr>
                <tr className="border-b border-slate-100 dark:border-slate-800">
                  <td className="p-3 font-medium text-blue-600">MNDWI</td>
                  <td className="p-3 font-mono text-xs">(Green - SWIR1) / (Green + SWIR1)</td>
                  <td className="p-3">-1 a 1</td>
                  <td className="p-3">Agua turbia</td>
                </tr>
                <tr className="border-b border-slate-100 dark:border-slate-800">
                  <td className="p-3 font-medium text-green-600">NDVI</td>
                  <td className="p-3 font-mono text-xs">(NIR - Red) / (NIR + Red)</td>
                  <td className="p-3">-1 a 1</td>
                  <td className="p-3">Vegetación</td>
                </tr>
                <tr className="border-b border-slate-100 dark:border-slate-800">
                  <td className="p-3 font-medium text-green-600">NDMI</td>
                  <td className="p-3 font-mono text-xs">(NIR - SWIR1) / (NIR + SWIR1)</td>
                  <td className="p-3">-1 a 1</td>
                  <td className="p-3">Humedad en vegetación</td>
                </tr>
                <tr className="border-b border-slate-100 dark:border-slate-800">
                  <td className="p-3 font-medium text-orange-600">NDSI</td>
                  <td className="p-3 font-mono text-xs">(Green - SWIR2) / (Green + SWIR2)</td>
                  <td className="p-3">-1 a 1</td>
                  <td className="p-3">Suelos salinos</td>
                </tr>
                <tr className="border-b border-slate-100 dark:border-slate-800">
                  <td className="p-3 font-medium text-orange-600">Salinity Index</td>
                  <td className="p-3 font-mono text-xs">SWIR2 / (SWIR2 + NIR)</td>
                  <td className="p-3">0 a 1</td>
                  <td className="p-3">Salinización</td>
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Sección 4: Preguntas frecuentes */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            Preguntas Frecuentes
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Pregunta 1 */}
          <div className="border-l-4 border-blue-500 pl-4">
            <h3 className="text-lg font-semibold mb-3">
              ¿Más imágenes mejoran la accuracy?
            </h3>
            <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
              <p className="font-semibold text-amber-800 mb-2">Respuesta: PARCIALMENTE</p>
              <div className="space-y-3">
                <div>
                  <p className="font-medium text-slate-900 dark:text-white mb-1">Beneficios:</p>
                  <ul className="space-y-1 text-sm text-slate-600 dark:text-slate-400 ml-4">
                    <li>• Mejor cobertura temporal: más imágenes = más probabilidad de capturar eventos extremos</li>
                    <li>• Mayor precisión en tendencias: intervalos más pequeños = tendencias más precisas</li>
                    <li>• Reducción de ruido: más imágenes = mayor robustez estadística</li>
                  </ul>
                </div>
                <div>
                  <p className="font-medium text-slate-900 dark:text-white mb-1">Limitaciones:</p>
                  <ul className="space-y-1 text-sm text-slate-600 dark:text-slate-400 ml-4">
                    <li>• NO hace promedios temporales: cada imagen se analiza independientemente</li>
                    <li>• NO mejora la accuracy de clasificación: depende de umbrales fijos, no de cantidad de imágenes</li>
                    <li>• NO hace promedios ponderados: el promedio es aritmético simple</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Pregunta 2 */}
          <div className="border-l-4 border-green-500 pl-4">
            <h3 className="text-lg font-semibold mb-3">
              ¿Hace un promedio?
            </h3>
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
              <p className="font-semibold text-green-800 mb-2">Respuesta: SÍ</p>
              <div className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
                <p className="font-medium mb-1">Tipo de promedio:</p>
                <ul className="space-y-1 ml-4">
                  <li>• Promedio aritmético simple</li>
                  <li>• NO ponderado</li>
                  <li>• NO filtrado</li>
                </ul>
                <div className="mt-3 p-3 bg-white dark:bg-slate-900 rounded border border-slate-200 dark:border-slate-700">
                  <p className="font-mono text-xs">
                    avg_water = (water_1 + water_2 + ... + water_n) / n
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Pregunta 3 */}
          <div className="border-l-4 border-purple-500 pl-4">
            <h3 className="text-lg font-semibold mb-3">
              ¿Es ponderado?
            </h3>
            <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
              <p className="font-semibold text-purple-800 mb-2">Respuesta: NO</p>
              <div className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
                <p className="font-medium mb-1">Características:</p>
                <ul className="space-y-1 ml-4">
                  <li>• Todas las imágenes tienen el mismo peso en el promedio</li>
                  <li>• NO hay ponderación por calidad de imagen</li>
                  <li>• NO hay ponderación por nubosidad</li>
                  <li>• NO hay ponderación por resolución</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Pregunta 4 */}
          <div className="border-l-4 border-slate-500 pl-4">
            <h3 className="text-lg font-semibold mb-3">
              ¿Cómo calcula los resultados?
            </h3>
            <div className="bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-4">
              <div className="space-y-3">
                <div>
                  <p className="font-medium text-slate-900 dark:text-white mb-2">Para cada fecha (imagen individual):</p>
                  <ol className="space-y-1 text-sm text-slate-600 dark:text-slate-400 ml-4 list-decimal">
                    <li>Clasificación píxel a píxel usando umbrales de índices espectrales</li>
                    <li>Conteo de píxeles de cada clase dentro de la parcela</li>
                    <li>Conversión a hectáreas: count × 100 m² ÷ 10,000</li>
                  </ol>
                </div>
                <div>
                  <p className="font-medium text-slate-900 dark:text-white mb-2">Para el resumen (todas las imágenes):</p>
                  <ol className="space-y-1 text-sm text-slate-600 dark:text-slate-400 ml-4 list-decimal">
                    <li>Promedios aritméticos simples de todas las imágenes</li>
                    <li>Tendencias: comparan primera vs última imagen</li>
                    <li>Clasificación: up, down, o stable con umbral de 1 ha</li>
                  </ol>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Sección 5: Tendencias */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-600" />
            Interpretación de Tendencias
          </CardTitle>
          <CardDescription>
            Cómo interpretar las flechas de tendencia en el resumen
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp className="w-6 h-6 text-blue-600" />
                <h4 className="font-bold text-blue-600">Aumentando</h4>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                El área está aumentando con el tiempo. Indica un problema creciente de anegamiento o salinización.
              </p>
            </div>

            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <TrendingDown className="w-6 h-6 text-green-600" />
                <h4 className="font-bold text-green-600">Disminuyendo</h4>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                El área está disminuyendo con el tiempo. Indica que la situación está mejorando.
              </p>
            </div>

            <div className="bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <Minus className="w-6 h-6 text-slate-600" />
                <h4 className="font-bold text-slate-600">Estable</h4>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                El área se mantiene constante. No hay cambios significativos en el período analizado.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Sección 6: Recomendaciones */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Info className="w-5 h-5 text-purple-600" />
            Recomendaciones para Mejorar la Accuracy
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
              <h4 className="font-semibold text-purple-800 mb-3">1. Ajustar umbrales</h4>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                Los umbrales actuales están ajustados para humedales de Argentina. Pueden no ser óptimos para otros tipos de suelo.
              </p>
              <div className="text-sm text-slate-600 dark:text-slate-400">
                <p className="font-medium mb-1">Cómo ajustar:</p>
                <ul className="space-y-1 ml-4">
                  <li>• Calibrar con datos de campo</li>
                  <li>• Usar validación cruzada</li>
                  <li>• Ajustar por tipo de suelo</li>
                  <li>• Considerar estacionalidad</li>
                </ul>
              </div>
            </div>

            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <h4 className="font-semibold text-blue-800 mb-3">2. Aumentar muestras por año</h4>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                De 4 a 8 o 12 para mejor cobertura temporal.
              </p>
              <div className="text-sm text-slate-600 dark:text-slate-400">
                <p className="font-medium mb-1">Beneficios:</p>
                <ul className="space-y-1 ml-4">
                  <li>• Mayor probabilidad de capturar eventos extremos</li>
                  <li>• Tendencias más precisas</li>
                  <li>• Mejor cobertura temporal</li>
                </ul>
              </div>
            </div>

            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
              <h4 className="font-semibold text-green-800 mb-3">3. Reducir nubosidad máxima</h4>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                De 20% a 10% o 5% para mejor calidad de imágenes.
              </p>
              <div className="text-sm text-slate-600 dark:text-slate-400">
                <p className="font-medium mb-1">Trade-off:</p>
                <ul className="space-y-1 ml-4">
                  <li>• Mejor calidad de imágenes</li>
                  <li>• Menor interferencia de nubes</li>
                  <li>• Clasificación más precisa</li>
                  <li>• Pero menos imágenes disponibles</li>
                </ul>
              </div>
            </div>

            <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
              <h4 className="font-semibold text-amber-800 mb-3">4. Validación con datos de campo</h4>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                Comparar mediciones satelitales con mediciones in situ.
              </p>
              <div className="text-sm text-slate-600 dark:text-slate-400">
                <p className="font-medium mb-1">Métricas de validación:</p>
                <ul className="space-y-1 ml-4">
                  <li>• RMSE (Root Mean Square Error)</li>
                  <li>• MAE (Mean Absolute Error)</li>
                  <li>• R² (Coeficiente de determinación)</li>
                  <li>• Accuracy (% de píxeles correctamente clasificados)</li>
                </ul>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Footer */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="text-sm text-slate-600 dark:text-slate-400">
              <p>Para más información técnica, consulta la documentación completa:</p>
              <a href="/docs/analizador-satelital.md" className="text-blue-600 hover:underline">
                docs/analizador-satelital.md
              </a>
            </div>
            <Button variant="outline" asChild>
              <Link href="/satelite">
                <Satellite className="w-4 h-4 mr-2" />
                Volver al Análisis
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
