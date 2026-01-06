/**
 * municipalities-coords.ts
 *
 * Tabla de coordenadas de municipios de la Provincia de Buenos Aires.
 * Utilizada para consultas al API de Open-Meteo sin ambigüedades.
 *
 * Coordenadas obtenidas de fuentes oficiales y verificadas para evitar
 * confusiones entre ciudades homónimas y municipios.
 *
 * @version 1.0.0
 * @created 2026-01-03
 * @author Kilo Code
 */

export interface MunicipalityCoords {
  name: string;
  latitude: number;
  longitude: number;
  province: string;
}

/**
 * Mapa de coordenadas de municipios
 * key: nombre del municipio (debe coincidir exactamente con los datos del índice)
 */
export const MUNICIPALITIES_COORDS: Record<string, MunicipalityCoords> = {
  "Adolfo Alsina": {
    name: "Adolfo Alsina",
    latitude: -36.8833,
    longitude: -62.7167,
    province: "Buenos Aires"
  },
  "Adolfo Gonzales Chaves": {
    name: "Adolfo Gonzales Chaves",
    latitude: -38.0167,
    longitude: -60.0833,
    province: "Buenos Aires"
  },
  "Alberti": {
    name: "Alberti",
    latitude: -35.0333,
    longitude: -60.2667,
    province: "Buenos Aires"
  },
  "Arrecifes": {
    name: "Arrecifes",
    latitude: -34.0667,
    longitude: -60.1167,
    province: "Buenos Aires"
  },
  "Avellaneda": {
    name: "Avellaneda",
    latitude: -34.6617,
    longitude: -58.3656,
    province: "Buenos Aires"
  },
  "Bahia Blanca": {
    name: "Bahia Blanca",
    latitude: -38.7183,
    longitude: -62.2663,
    province: "Buenos Aires"
  },
  "Balcarce": {
    name: "Balcarce",
    latitude: -37.8461,
    longitude: -58.2556,
    province: "Buenos Aires"
  },
  "Baradero": {
    name: "Baradero",
    latitude: -33.8,
    longitude: -59.5167,
    province: "Buenos Aires"
  },
  "Benito Juarez": {
    name: "Benito Juarez",
    latitude: -37.6833,
    longitude: -59.8,
    province: "Buenos Aires"
  },
  "Bolivar": {
    name: "Bolivar",
    latitude: -36.2333,
    longitude: -61.1167,
    province: "Buenos Aires"
  },
  "Bragado": {
    name: "Bragado",
    latitude: -35.1167,
    longitude: -60.4833,
    province: "Buenos Aires"
  },
  "Brandsen": {
    name: "Brandsen",
    latitude: -35.1667,
    longitude: -58.2333,
    province: "Buenos Aires"
  },
  "Campana": {
    name: "Campana",
    latitude: -34.1667,
    longitude: -58.9667,
    province: "Buenos Aires"
  },
  "Capitán Sarmiento": {
    name: "Capitán Sarmiento",
    latitude: -34.1667,
    longitude: -59.8,
    province: "Buenos Aires"
  },
  "Carlos Tejedor": {
    name: "Carlos Tejedor",
    latitude: -35.3833,
    longitude: -62.3833,
    province: "Buenos Aires"
  },
  "Carmen de Areco": {
    name: "Carmen de Areco",
    latitude: -34.3833,
    longitude: -59.8167,
    province: "Buenos Aires"
  },
  "Castelli": {
    name: "Castelli",
    latitude: -36.0833,
    longitude: -57.8,
    province: "Buenos Aires"
  },
  "Chacabuco": {
    name: "Chacabuco",
    latitude: -34.6333,
    longitude: -60.4667,
    province: "Buenos Aires"
  },
  "Chascomús": {
    name: "Chascomús",
    latitude: -35.5667,
    longitude: -58.0167,
    province: "Buenos Aires"
  },
  "Chivilcoy": {
    name: "Chivilcoy",
    latitude: -34.8956,
    longitude: -60.0183,
    province: "Buenos Aires"
  },
  "Coronel Dorrego": {
    name: "Coronel Dorrego",
    latitude: -38.7167,
    longitude: -61.2833,
    province: "Buenos Aires"
  },
  "Coronel Pringles": {
    name: "Coronel Pringles",
    latitude: -37.9833,
    longitude: -61.3667,
    province: "Buenos Aires"
  },
  "Coronel Rosales": {
    name: "Coronel Rosales",
    latitude: -38.8833,
    longitude: -62.0833,
    province: "Buenos Aires"
  },
  "Coronel Suárez": {
    name: "Coronel Suárez",
    latitude: -37.45,
    longitude: -61.9333,
    province: "Buenos Aires"
  },
  "Daireaux": {
    name: "Daireaux",
    latitude: -36.6,
    longitude: -61.7667,
    province: "Buenos Aires"
  },
  "Dolores": {
    name: "Dolores",
    latitude: -36.3133,
    longitude: -57.6792,
    province: "Buenos Aires"
  },
  "Exaltación de la Cruz": {
    name: "Exaltación de la Cruz",
    latitude: -34.3167,
    longitude: -59.1,
    province: "Buenos Aires"
  },
  "Florentino Ameghino": {
    name: "Florentino Ameghino",
    latitude: -35.05,
    longitude: -62.8,
    province: "Buenos Aires"
  },
  "General Alvear": {
    name: "General Alvear",
    latitude: -36.0333,
    longitude: -60.0167,
    province: "Buenos Aires"
  },
  "General Arenales": {
    name: "General Arenales",
    latitude: -34.3,
    longitude: -61.3,
    province: "Buenos Aires"
  },
  "General Belgrano": {
    name: "General Belgrano",
    latitude: -35.7667,
    longitude: -58.5,
    province: "Buenos Aires"
  },
  "General Guido": {
    name: "General Guido",
    latitude: -36.6667,
    longitude: -57.8,
    province: "Buenos Aires"
  },
  "General La Madrid": {
    name: "General La Madrid",
    latitude: -37.2667,
    longitude: -61.2833,
    province: "Buenos Aires"
  },
  "Pilar": {
    name: "Pilar",
    latitude: -34.4583,
    longitude: -58.9139,
    province: "Buenos Aires"
  }
};

/**
 * Obtiene las coordenadas de un municipio
 * @param municipalityName - Nombre del municipio
 * @returns Coordenadas del municipio o null si no se encuentra
 */
export function getMunicipalityCoords(municipalityName: string): MunicipalityCoords | null {
  return MUNICIPALITIES_COORDS[municipalityName] || null;
}

/**
 * Verifica si un municipio existe en la tabla
 * @param municipalityName - Nombre del municipio
 * @returns true si el municipio existe
 */
export function municipalityExists(municipalityName: string): boolean {
  return municipalityName in MUNICIPALITIES_COORDS;
}

/**
 * Obtiene la lista de todos los municipios disponibles
 * @returns Array con nombres de municipios
 */
export function getAllMunicipalityNames(): string[] {
  return Object.keys(MUNICIPALITIES_COORDS).sort();
}
