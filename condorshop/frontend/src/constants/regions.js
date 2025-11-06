export const REGIONS = [
  { value: 'arica', label: 'Arica y Parinacota' },
  { value: 'tarapaca', label: 'Tarapacá' },
  { value: 'antofagasta', label: 'Antofagasta' },
  { value: 'atacama', label: 'Atacama' },
  { value: 'coquimbo', label: 'Coquimbo' },
  { value: 'valparaiso', label: 'Valparaíso' },
  { value: 'metropolitana', label: 'Región Metropolitana' },
  { value: 'ohiggins', label: "O'Higgins" },
  { value: 'maule', label: 'Maule' },
  { value: 'nuble', label: 'Ñuble' },
  { value: 'biobio', label: 'Biobío' },
  { value: 'araucania', label: 'La Araucanía' },
  { value: 'rios', label: 'Los Ríos' },
  { value: 'lagos', label: 'Los Lagos' },
  { value: 'aysen', label: 'Aysén' },
  { value: 'magallanes', label: 'Magallanes' },
]

export const getRegionLabel = (value) => {
  if (!value) {
    return ''
  }

  const normalized = value.toLowerCase()
  const match = REGIONS.find((region) => region.value === normalized)
  return match?.label || value
}

export const matchRegionValue = (labelOrValue) => {
  if (!labelOrValue) {
    return ''
  }

  const normalized = labelOrValue.toLowerCase()

  const exactMatch = REGIONS.find(
    (region) => region.value === normalized || region.label.toLowerCase() === normalized,
  )

  if (exactMatch) {
    return exactMatch.value
  }

  const partialMatch = REGIONS.find(
    (region) =>
      region.label.toLowerCase().includes(normalized) || normalized.includes(region.value),
  )

  return partialMatch?.value || labelOrValue
}

