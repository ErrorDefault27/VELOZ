import { useCallback, useEffect, useRef, useState } from 'react'
import {
  ApiError,
  createIngredient,
  deleteIngredient,
  listIngredients,
  updateIngredient,
} from '../api'
import { formatDateForDisplay, formatDecimalForDisplay } from '../display'
import type { ApiFieldErrors, Ingredient, IngredientInput, Unit } from '../types'
import { IngredientForm } from './IngredientForm'

type IngredientsSectionProps = {
  onIngredientsChanged: () => void
}

type Notice = { type: 'success' | 'error'; message: string }

const unitLabels: Record<Unit, string> = { kg: 'Kg', l: 'L', un: 'un' }
const nameCollator = new Intl.Collator('pt-BR', { sensitivity: 'base' })

function sortIngredients(ingredients: Ingredient[]): Ingredient[] {
  return ingredients.toSorted((left, right) => {
    const byName = nameCollator.compare(left.nome, right.nome)
    return byName || left.nome.localeCompare(right.nome) || left.id - right.id
  })
}

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError'
}

export function IngredientsSection({
  onIngredientsChanged,
}: IngredientsSectionProps) {
  const [ingredients, setIngredients] = useState<Ingredient[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [editor, setEditor] = useState<'new' | Ingredient | null>(null)
  const [fieldErrors, setFieldErrors] = useState<ApiFieldErrors>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [notice, setNotice] = useState<Notice | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const submissionInFlight = useRef(false)

  const load = useCallback(async (signal?: AbortSignal) => {
    try {
      const data = await listIngredients(signal)
      setIngredients(data)
      setLoadError(null)
    } catch (error) {
      if (isAbortError(error)) {
        return
      }
      setLoadError(
        error instanceof ApiError
          ? error.message
          : 'Não foi possível carregar os ingredientes.',
      )
    } finally {
      if (!signal?.aborted) {
        setIsLoading(false)
      }
    }
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    // State changes happen only after the request settles.
    // oxlint-disable-next-line react/set-state-in-effect
    void load(controller.signal)
    return () => controller.abort()
  }, [load])

  function openCreateForm() {
    setEditor('new')
    setFieldErrors({})
    setFormError(null)
    setNotice(null)
  }

  function openEditForm(ingredient: Ingredient) {
    setEditor(ingredient)
    setFieldErrors({})
    setFormError(null)
    setNotice(null)
  }

  function closeForm() {
    setEditor(null)
    setFieldErrors({})
    setFormError(null)
  }

  function clearFieldError(field: keyof IngredientInput) {
    setFormError(null)
    setFieldErrors((current) => {
      if (!current[field]) {
        return current
      }
      const next = { ...current }
      delete next[field]
      return next
    })
  }

  async function handleSave(input: IngredientInput) {
    if (submissionInFlight.current) {
      return
    }

    submissionInFlight.current = true
    setIsSubmitting(true)
    setFieldErrors({})
    setFormError(null)

    try {
      const saved =
        editor !== null && editor !== 'new'
          ? await updateIngredient(editor.id, input)
          : await createIngredient(input)

      setIngredients((current) => {
        const withoutSaved = current.filter((item) => item.id !== saved.id)
        return sortIngredients([...withoutSaved, saved])
      })
      setEditor(null)
      setNotice({
        type: 'success',
        message:
          editor === 'new'
            ? 'Ingrediente cadastrado com sucesso.'
            : 'Ingrediente atualizado com sucesso.',
      })
      onIngredientsChanged()
    } catch (error) {
      if (error instanceof ApiError) {
        setFieldErrors(error.fieldErrors)
        const hasEditableFieldError = Object.keys(error.fieldErrors).some(
          (field) => field !== 'detail',
        )
        setFormError(
          hasEditableFieldError
            ? 'Revise os campos destacados e tente novamente.'
            : error.message,
        )
      } else {
        setFormError('Não foi possível salvar o ingrediente.')
      }
    } finally {
      submissionInFlight.current = false
      setIsSubmitting(false)
    }
  }

  async function handleDelete(ingredient: Ingredient) {
    const confirmed = window.confirm(
      `Excluir “${ingredient.nome}”? Esta ação não pode ser desfeita.`,
    )
    if (!confirmed || deletingId !== null) {
      return
    }

    setDeletingId(ingredient.id)
    setNotice(null)
    try {
      await deleteIngredient(ingredient.id)
      setIngredients((current) =>
        current.filter((item) => item.id !== ingredient.id),
      )
      if (editor !== 'new' && editor?.id === ingredient.id) {
        closeForm()
      }
      setNotice({
        type: 'success',
        message: `Ingrediente “${ingredient.nome}” excluído.`,
      })
      onIngredientsChanged()
    } catch (error) {
      setNotice({
        type: 'error',
        message:
          error instanceof ApiError
            ? error.message
            : 'Não foi possível excluir o ingrediente.',
      })
    } finally {
      setDeletingId(null)
    }
  }

  function retryLoad() {
    setIsLoading(true)
    setLoadError(null)
    void load()
  }

  return (
    <section className="panel ingredients-panel" aria-labelledby="ingredients-title">
      <div className="section-heading">
        <div>
          <p className="section-kicker">Estoque do período</p>
          <h2 id="ingredients-title">Ingredientes</h2>
          <p>Cadastre a fotografia atual usada pelo cálculo de reposição.</p>
        </div>
        <button className="button" type="button" onClick={openCreateForm}>
          + Novo ingrediente
        </button>
      </div>

      {notice ? (
        <div
          className={`notice notice--${notice.type}`}
          role={notice.type === 'error' ? 'alert' : 'status'}
        >
          {notice.message}
        </div>
      ) : null}

      {editor ? (
        <IngredientForm
          key={editor === 'new' ? 'new' : editor.id}
          ingredient={editor === 'new' ? null : editor}
          fieldErrors={fieldErrors}
          formError={formError}
          isSubmitting={isSubmitting}
          onCancel={closeForm}
          onFieldChange={clearFieldError}
          onSubmit={handleSave}
        />
      ) : null}

      {isLoading ? (
        <div className="state-box" role="status">
          <span className="spinner" aria-hidden="true" />
          Carregando ingredientes…
        </div>
      ) : loadError ? (
        <div className="state-box state-box--error" role="alert">
          <div>
            <strong>Falha ao carregar ingredientes</strong>
            <p>{loadError}</p>
          </div>
          <button className="button button--secondary" type="button" onClick={retryLoad}>
            Tentar novamente
          </button>
        </div>
      ) : ingredients.length === 0 ? (
        <div className="empty-state">
          <strong>Nenhum ingrediente cadastrado</strong>
          <p>Cadastre o primeiro item para começar a gerar a lista de compras.</p>
          <button className="button" type="button" onClick={openCreateForm}>
            Cadastrar ingrediente
          </button>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th scope="col">Ingrediente</th>
                <th scope="col">Unidade</th>
                <th scope="col">Meta</th>
                <th scope="col">Qtd. inicial</th>
                <th scope="col">Consumo</th>
                <th scope="col">Estoque atual</th>
                <th scope="col">Validade</th>
                <th scope="col">Falta antecipada</th>
                <th scope="col"><span className="visually-hidden">Ações</span></th>
              </tr>
            </thead>
            <tbody>
              {ingredients.map((ingredient) => (
                <tr key={ingredient.id}>
                  <td data-label="Ingrediente">
                    <strong>{ingredient.nome}</strong>
                  </td>
                  <td data-label="Unidade">{unitLabels[ingredient.unidade]}</td>
                  <td data-label="Meta">
                    {formatDecimalForDisplay(ingredient.meta_estoque)}
                  </td>
                  <td data-label="Qtd. inicial">
                    {formatDecimalForDisplay(ingredient.quantidade_inicial)}
                  </td>
                  <td data-label="Consumo">
                    {formatDecimalForDisplay(ingredient.consumo_periodo)}
                  </td>
                  <td data-label="Estoque atual">
                    <span className="stock-value">
                      {formatDecimalForDisplay(ingredient.estoque_atual)}
                    </span>
                  </td>
                  <td data-label="Validade">
                    <time dateTime={ingredient.data_validade}>
                      {formatDateForDisplay(ingredient.data_validade)}
                    </time>
                  </td>
                  <td data-label="Falta antecipada">
                    <span
                      className={`tag ${
                        ingredient.acabou_antes_fim_mes ? 'tag--warning' : ''
                      }`}
                    >
                      {ingredient.acabou_antes_fim_mes ? 'Sim' : 'Não'}
                    </span>
                  </td>
                  <td className="row-actions" data-label="Ações">
                    <button
                      className="text-button"
                      type="button"
                      onClick={() => openEditForm(ingredient)}
                    >
                      Editar
                    </button>
                    <button
                      className="text-button text-button--danger"
                      type="button"
                      onClick={() => void handleDelete(ingredient)}
                      disabled={deletingId !== null}
                      aria-label={`Excluir ${ingredient.nome}`}
                    >
                      {deletingId === ingredient.id ? 'Excluindo…' : 'Excluir'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
