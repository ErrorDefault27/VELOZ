import type {
  ApiFieldErrors,
  Ingredient,
  IngredientInput,
  PurchaseList,
} from './types'

type ErrorPayload = Record<string, unknown>

export class ApiError extends Error {
  readonly status: number | null
  readonly fieldErrors: ApiFieldErrors

  constructor(
    message: string,
    options: { status?: number | null; fieldErrors?: ApiFieldErrors } = {},
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = options.status ?? null
    this.fieldErrors = options.fieldErrors ?? {}
  }
}

function toFieldErrors(payload: unknown): ApiFieldErrors {
  if (typeof payload !== 'object' || payload === null || Array.isArray(payload)) {
    return {}
  }

  const errors: ApiFieldErrors = {}
  for (const [field, value] of Object.entries(payload as ErrorPayload)) {
    if (Array.isArray(value)) {
      const messages = value.filter(
        (message): message is string => typeof message === 'string',
      )
      if (messages.length > 0) {
        errors[field] = messages
      }
    } else if (typeof value === 'string') {
      errors[field] = [value]
    }
  }
  return errors
}

function firstError(errors: ApiFieldErrors): string | undefined {
  for (const messages of Object.values(errors)) {
    if (messages[0]) {
      return messages[0]
    }
  }
  return undefined
}

async function request<T>(url: string, options: RequestInit = {}): Promise<T> {
  let response: Response
  try {
    response = await fetch(url, {
      ...options,
      headers: {
        Accept: 'application/json',
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...options.headers,
      },
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw error
    }
    throw new ApiError(
      'Não foi possível conectar à API. Confira se o backend está em execução.',
    )
  }

  if (response.status === 204) {
    return undefined as T
  }

  let payload: unknown
  try {
    payload = await response.json()
  } catch {
    if (!response.ok) {
      throw new ApiError(`A API respondeu com o status ${response.status}.`, {
        status: response.status,
      })
    }
    throw new ApiError('A API retornou uma resposta inválida.', {
      status: response.status,
    })
  }

  if (!response.ok) {
    const fieldErrors = toFieldErrors(payload)
    throw new ApiError(
      firstError(fieldErrors) ?? `A API respondeu com o status ${response.status}.`,
      { status: response.status, fieldErrors },
    )
  }

  return payload as T
}

export function listIngredients(signal?: AbortSignal): Promise<Ingredient[]> {
  return request<Ingredient[]>('/api/ingredientes/', { signal })
}

export function createIngredient(input: IngredientInput): Promise<Ingredient> {
  return request<Ingredient>('/api/ingredientes/', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export function updateIngredient(
  id: number,
  input: Partial<IngredientInput>,
): Promise<Ingredient> {
  return request<Ingredient>(`/api/ingredientes/${id}/`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  })
}

export function deleteIngredient(id: number): Promise<void> {
  return request<void>(`/api/ingredientes/${id}/`, { method: 'DELETE' })
}

export function getPurchases(
  referenceDate: string,
  signal?: AbortSignal,
): Promise<PurchaseList> {
  const query = new URLSearchParams({ data_referencia: referenceDate })
  return request<PurchaseList>(`/api/compras/?${query.toString()}`, { signal })
}
