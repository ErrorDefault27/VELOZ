import type { ReplenishmentReason } from './types'

export const REASON_LABELS: Record<ReplenishmentReason, string> = {
  vencimento: 'Estoque vencido',
  falta_antecipada: 'Falta antecipada',
  reposicao_normal: 'Reposição normal',
  estoque_suficiente: 'Estoque suficiente',
}

export function formatDecimalForDisplay(value: string): string {
  const [integerPart, decimalPart = ''] = value.split('.')
  const trimmedDecimals = decimalPart.replace(/0+$/, '')
  const groupedInteger = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, '.')
  return trimmedDecimals ? `${groupedInteger},${trimmedDecimals}` : groupedInteger
}

export function formatDateForDisplay(value: string): string {
  const [year, month, day] = value.split('-')
  return year && month && day ? `${day}/${month}/${year}` : value
}

export function localDateInputValue(now = new Date()): string {
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
