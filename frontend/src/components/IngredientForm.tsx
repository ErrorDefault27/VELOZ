import { useId, useState, type FormEvent } from 'react'
import type {
  ApiFieldErrors,
  Ingredient,
  IngredientInput,
  Unit,
} from '../types'

type IngredientFormProps = {
  ingredient: Ingredient | null
  fieldErrors: ApiFieldErrors
  formError: string | null
  isSubmitting: boolean
  onCancel: () => void
  onFieldChange: (field: keyof IngredientInput) => void
  onSubmit: (input: IngredientInput) => Promise<void>
}

function initialValues(ingredient: Ingredient | null): IngredientInput {
  if (ingredient) {
    return {
      nome: ingredient.nome,
      unidade: ingredient.unidade,
      meta_estoque: ingredient.meta_estoque,
      quantidade_inicial: ingredient.quantidade_inicial,
      consumo_periodo: ingredient.consumo_periodo,
      data_validade: ingredient.data_validade,
      acabou_antes_fim_mes: ingredient.acabou_antes_fim_mes,
    }
  }

  return {
    nome: '',
    unidade: 'kg',
    meta_estoque: '',
    quantidade_inicial: '',
    consumo_periodo: '',
    data_validade: '',
    acabou_antes_fim_mes: false,
  }
}

function FieldErrors({ id, messages }: { id: string; messages?: string[] }) {
  if (!messages?.length) {
    return null
  }

  return (
    <div className="field-errors" id={id} role="alert">
      {messages.map((message) => (
        <span key={message}>{message}</span>
      ))}
    </div>
  )
}

export function IngredientForm({
  ingredient,
  fieldErrors,
  formError,
  isSubmitting,
  onCancel,
  onFieldChange,
  onSubmit,
}: IngredientFormProps) {
  const formId = useId()
  const [values, setValues] = useState<IngredientInput>(() =>
    initialValues(ingredient),
  )

  function updateField<Field extends keyof IngredientInput>(
    field: Field,
    value: IngredientInput[Field],
  ) {
    setValues((current) => ({ ...current, [field]: value }))
    onFieldChange(field)
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void onSubmit(values)
  }

  const describedBy = (field: keyof IngredientInput, helpId?: string) => {
    const ids = [helpId, fieldErrors[field] ? `${formId}-${field}-error` : undefined]
    return ids.filter(Boolean).join(' ') || undefined
  }

  return (
    <form className="ingredient-form" onSubmit={handleSubmit} noValidate>
      <div className="form-heading">
        <div>
          <p className="section-kicker">{ingredient ? 'Edição' : 'Cadastro'}</p>
          <h3>{ingredient ? `Editar ${ingredient.nome}` : 'Novo ingrediente'}</h3>
        </div>
        <button
          className="button button--ghost button--small"
          type="button"
          onClick={onCancel}
          disabled={isSubmitting}
        >
          Fechar
        </button>
      </div>

      {formError ? (
        <div className="notice notice--error" role="alert">
          {formError}
        </div>
      ) : null}

      <div className="form-grid">
        <div className="form-field form-field--wide">
          <label htmlFor={`${formId}-nome`}>Nome do ingrediente</label>
          <input
            id={`${formId}-nome`}
            name="nome"
            value={values.nome}
            onChange={(event) => updateField('nome', event.target.value)}
            aria-invalid={Boolean(fieldErrors.nome)}
            aria-describedby={describedBy('nome')}
            autoComplete="off"
            disabled={isSubmitting}
          />
          <FieldErrors id={`${formId}-nome-error`} messages={fieldErrors.nome} />
        </div>

        <div className="form-field">
          <label htmlFor={`${formId}-unidade`}>Unidade</label>
          <select
            id={`${formId}-unidade`}
            name="unidade"
            value={values.unidade}
            onChange={(event) => updateField('unidade', event.target.value as Unit)}
            aria-invalid={Boolean(fieldErrors.unidade)}
            aria-describedby={describedBy('unidade')}
            disabled={isSubmitting}
          >
            <option value="kg">Kg — quilograma</option>
            <option value="l">L — litro</option>
            <option value="un">un — unidade</option>
          </select>
          <FieldErrors
            id={`${formId}-unidade-error`}
            messages={fieldErrors.unidade}
          />
        </div>

        <div className="form-field">
          <label htmlFor={`${formId}-meta`}>Meta de estoque</label>
          <input
            id={`${formId}-meta`}
            name="meta_estoque"
            value={values.meta_estoque}
            onChange={(event) => updateField('meta_estoque', event.target.value)}
            inputMode="decimal"
            placeholder={values.unidade === 'un' ? '0' : '0.000'}
            aria-invalid={Boolean(fieldErrors.meta_estoque)}
            aria-describedby={describedBy('meta_estoque')}
            disabled={isSubmitting}
          />
          <FieldErrors
            id={`${formId}-meta_estoque-error`}
            messages={fieldErrors.meta_estoque}
          />
        </div>

        <div className="form-field">
          <label htmlFor={`${formId}-inicial`}>Quantidade inicial</label>
          <input
            id={`${formId}-inicial`}
            name="quantidade_inicial"
            value={values.quantidade_inicial}
            onChange={(event) =>
              updateField('quantidade_inicial', event.target.value)
            }
            inputMode="decimal"
            placeholder={values.unidade === 'un' ? '0' : '0.000'}
            aria-invalid={Boolean(fieldErrors.quantidade_inicial)}
            aria-describedby={describedBy(
              'quantidade_inicial',
              `${formId}-inicial-help`,
            )}
            disabled={isSubmitting}
          />
          <small id={`${formId}-inicial-help`}>
            Quantidade disponível no começo do período, antes do consumo.
          </small>
          <FieldErrors
            id={`${formId}-quantidade_inicial-error`}
            messages={fieldErrors.quantidade_inicial}
          />
        </div>

        <div className="form-field">
          <label htmlFor={`${formId}-consumo`}>Consumo do período</label>
          <input
            id={`${formId}-consumo`}
            name="consumo_periodo"
            value={values.consumo_periodo}
            onChange={(event) => updateField('consumo_periodo', event.target.value)}
            inputMode="decimal"
            placeholder={values.unidade === 'un' ? '0' : '0.000'}
            aria-invalid={Boolean(fieldErrors.consumo_periodo)}
            aria-describedby={describedBy('consumo_periodo')}
            disabled={isSubmitting}
          />
          <FieldErrors
            id={`${formId}-consumo_periodo-error`}
            messages={fieldErrors.consumo_periodo}
          />
        </div>

        <div className="form-field">
          <label htmlFor={`${formId}-validade`}>Data de validade</label>
          <input
            id={`${formId}-validade`}
            name="data_validade"
            type="date"
            value={values.data_validade}
            onChange={(event) => updateField('data_validade', event.target.value)}
            aria-invalid={Boolean(fieldErrors.data_validade)}
            aria-describedby={describedBy('data_validade')}
            disabled={isSubmitting}
          />
          <FieldErrors
            id={`${formId}-data_validade-error`}
            messages={fieldErrors.data_validade}
          />
        </div>

        <div className="form-field form-field--wide checkbox-field">
          <input
            id={`${formId}-falta`}
            name="acabou_antes_fim_mes"
            type="checkbox"
            checked={values.acabou_antes_fim_mes}
            onChange={(event) =>
              updateField('acabou_antes_fim_mes', event.target.checked)
            }
            aria-invalid={Boolean(fieldErrors.acabou_antes_fim_mes)}
            aria-describedby={describedBy(
              'acabou_antes_fim_mes',
              `${formId}-falta-help`,
            )}
            disabled={isSubmitting}
          />
          <div>
            <label htmlFor={`${formId}-falta`}>Acabou antes do fim do mês</label>
            <small id={`${formId}-falta-help`}>
              Marque somente quando o estoque atual for zero e houver consumo no
              período.
            </small>
            <FieldErrors
              id={`${formId}-acabou_antes_fim_mes-error`}
              messages={fieldErrors.acabou_antes_fim_mes}
            />
          </div>
        </div>
      </div>

      <p className="form-note">
        Use ponto como separador decimal. Para itens em “un”, informe somente números
        inteiros.
      </p>

      <div className="form-actions">
        <button
          className="button button--secondary"
          type="button"
          onClick={onCancel}
          disabled={isSubmitting}
        >
          Cancelar
        </button>
        <button className="button" type="submit" disabled={isSubmitting}>
          {isSubmitting
            ? 'Salvando…'
            : ingredient
              ? 'Salvar alterações'
              : 'Cadastrar ingrediente'}
        </button>
      </div>
    </form>
  )
}
