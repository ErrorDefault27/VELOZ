import { useState } from 'react'
import './App.css'
import { IngredientsSection } from './components/IngredientsSection'
import { ShoppingListSection } from './components/ShoppingListSection'

function App() {
  const [ingredientsRevision, setIngredientsRevision] = useState(0)

  return (
    <>
      <header className="site-header">
        <div className="page-width site-header__content">
          <a className="brand" href="#top" aria-label="Controle de estoque — início">
            <span className="brand__mark" aria-hidden="true">CE</span>
            <span>Controle de estoque</span>
          </a>
          <nav aria-label="Seções da página">
            <a href="#ingredientes">Ingredientes</a>
            <a href="#compras">Lista de compras</a>
          </nav>
        </div>
      </header>

      <main id="top" className="page-width app-shell">
        <div className="hero-copy">
          <p className="eyebrow">Planejamento mensal do restaurante</p>
          <h1>Estoque claro.<br />Compras objetivas.</h1>
          <p>
            Registre a situação de cada ingrediente e consulte a reposição calculada
            pelo backend.
          </p>
        </div>

        <div id="ingredientes">
          <IngredientsSection
            onIngredientsChanged={() =>
              setIngredientsRevision((current) => current + 1)
            }
          />
        </div>

        <div id="compras">
          <ShoppingListSection ingredientsRevision={ingredientsRevision} />
        </div>
      </main>

      <footer className="site-footer">
        <div className="page-width">
          Demonstração local — os cálculos são realizados pela API Django.
        </div>
      </footer>
    </>
  )
}

export default App
