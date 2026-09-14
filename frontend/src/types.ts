export type Unit = 'kg' | 'l' | 'un'

export type Ingredient = {
  id: number
  nome: string
  unidade: Unit
  meta_estoque: string
  quantidade_inicial: string
  consumo_periodo: string
  estoque_atual: string
  data_validade: string
  acabou_antes_fim_mes: boolean
}

export type IngredientInput = Omit<Ingredient, 'id' | 'estoque_atual'>

export type ReplenishmentReason =
  | 'vencimento'
  | 'falta_antecipada'
  | 'reposicao_normal'
  | 'estoque_suficiente'

export type Purchase = {
  id: number
  nome: string
  unidade: 'Kg' | 'L' | 'un'
  quantidade: string
  motivo: ReplenishmentReason
  texto: string
}

export type PurchaseList = {
  data_referencia: string
  compras: Purchase[]
}

export type ApiFieldErrors = Record<string, string[]>
