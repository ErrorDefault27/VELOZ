import { useEffect, useRef, useState, type FormEvent } from 'react'
import { ApiError, getPurchases } from '../api'
import { formatDateForDisplay, localDateInputValue, REASON_LABELS } from '../display'
import type { ApiFieldErrors, PurchaseList } from '../types'

type ShoppingListSectionProps = {
  ingredientsRevision: number
}

type PurchaseState =
  | { status: 'loading' }
  | { status: 'success'; data: PurchaseList }
  | { status: 'error'; message: string; fieldErrors: ApiFieldErrors }

export function ShoppingListSection({
  ingredientsRevision,
}: ShoppingListSectionProps) {
  const initialDate = localDateInputValue()
  const [dateInput, setDateInput] = useState(initialDate)
  const [requestedDate, setRequestedDate] = useState(initialDate)
  const [refreshVersion, setRefreshVersion] = useState(0)
  const [state, setState] = useState<PurchaseState>({ status: 'loading' })
  const requestSequence = useRef(0)
  const requestPending = useRef(true)

  useEffect(() => {
    const controller = new AbortController()
    const sequence = ++requestSequence.current
    requestPending.current = true
    // This effect synchronizes the view with the remote purchase resource.
    // oxlint-disable-next-line react/set-state-in-effect
    setState({ status: 'loading' })

    void getPurchases(requestedDate, controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) {
          setState({ status: 'success', data })
        }
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') {
          return
        }
        if (error instanceof ApiError) {
          setState({
            status: 'error',
            message: error.message,
            fieldErrors: error.fieldErrors,
          })
          return
        }
        setState({
          status: 'error',
          message: 'Não foi possível consultar a lista de compras.',
          fieldErrors: {},
        })
      })
      .finally(() => {
        if (sequence === requestSequence.current) {
          requestPending.current = false
        }
      })

    return () => controller.abort()
  }, [ingredientsRevision, refreshVersion, requestedDate])

  function handleRefresh(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (requestPending.current) {
      return
    }

    requestPending.current = true
    setState({ status: 'loading' })
    if (dateInput === requestedDate) {
      setRefreshVersion((current) => current + 1)
    } else {
      setRequestedDate(dateInput)
    }
  }

  const dateErrors = state.status === 'error' ? state.fieldErrors.data_referencia : null

  return (
    <section className="panel purchases-panel" aria-labelledby="purchases-title">
      <div className="section-heading section-heading--compact">
        <div>
          <p className="section-kicker">Sugestão calculada pelo backend</p>
          <h2 id="purchases-title">Lista de compras</h2>
          <p>Consulte o que precisa ser reposto na data escolhida.</p>
        </div>
      </div>

      <form className="purchase-toolbar" onSubmit={handleRefresh}>
        <div className="form-field purchase-date-field">
          <label htmlFor="purchase-reference-date">Data de referência</label>
          <input
            id="purchase-reference-date"
            name="data_referencia"
            type="date"
            value={dateInput}
            onChange={(event) => setDateInput(event.target.value)}
            aria-invalid={Boolean(dateErrors)}
            aria-describedby={dateErrors ? 'purchase-date-error' : undefined}
            disabled={state.status === 'loading'}
          />
          {dateErrors ? (
            <div className="field-errors" id="purchase-date-error" role="alert">
              {dateErrors.map((message) => (
                <span key={message}>{message}</span>
              ))}
            </div>
          ) : null}
        </div>
        <button className="button" type="submit" disabled={state.status === 'loading'}>
          {state.status === 'loading' ? 'Atualizando…' : 'Atualizar lista'}
        </button>
      </form>

      {state.status === 'loading' ? (
        <div className="state-box" role="status">
          <span className="spinner" aria-hidden="true" />
          Calculando lista de compras…
        </div>
      ) : state.status === 'error' ? (
        <div className="state-box state-box--error" role="alert">
          <div>
            <strong>Falha ao consultar compras</strong>
            <p>{state.message}</p>
          </div>
        </div>
      ) : (
        <div className="purchase-results">
          <p className="effective-date">
            Cálculo para{' '}
            <time dateTime={state.data.data_referencia}>
              {formatDateForDisplay(state.data.data_referencia)}
            </time>
          </p>

          {state.data.compras.length === 0 ? (
            <div className="empty-state empty-state--compact">
              <strong>Nada a comprar</strong>
              <p>Nenhuma reposição foi indicada para esta data de referência.</p>
            </div>
          ) : (
            <ul className="purchase-list">
              {state.data.compras.map((purchase) => (
                <li key={purchase.id}>
                  <div>
                    <strong>{purchase.texto}</strong>
                    <span>{purchase.nome}</span>
                  </div>
                  <span className={`reason reason--${purchase.motivo}`}>
                    {REASON_LABELS[purchase.motivo]}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  )
}
