/** Guía de usuario (/ayuda). Se carga en un bloque aparte (React.lazy): el
 * lector de Markdown, el buscador y el contenido solo se descargan al abrir
 * la guía. */
import { ArrowLeft, ArrowRight, BookOpen, Menu, Printer, Search, X } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Link, Navigate, Route, Routes, useLocation, useNavigate, useParams } from "react-router-dom";
import { TEXTO_DERECHOS } from "../lib/derechos";
import { buscar, type Resultado } from "./busqueda";
import { PAGINAS, buscarPagina, paginasDeSeccion, type Pagina } from "./contenido";
import { Contenido, analizar } from "./markdown";
import { SECCIONES } from "./secciones";
import styles from "./Guia.module.css";

const tituloSeccion = (slug: string) => SECCIONES.find((s) => s.slug === slug)?.titulo ?? slug;

function fechaLegible(iso: string): string {
  const [a, m, d] = iso.split("-").map(Number);
  if (!a || !m || !d) return iso;
  return new Date(a, m - 1, d).toLocaleDateString("es-CO", { day: "numeric", month: "long", year: "numeric" });
}

// ── Buscador (Ctrl+K) ───────────────────────────────────────────────────────

function Buscador({ abierto, onCerrar }: { abierto: boolean; onCerrar: () => void }) {
  const [consulta, setConsulta] = useState("");
  const [activo, setActivo] = useState(0);
  const entrada = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const resultados = useMemo<Resultado[]>(() => buscar(consulta), [consulta]);

  useEffect(() => {
    if (abierto) {
      setConsulta("");
      setActivo(0);
      setTimeout(() => entrada.current?.focus(), 0);
    }
  }, [abierto]);

  if (!abierto) return null;

  const ir = (r: Resultado) => {
    navigate(r.pagina.ruta + (r.ancla ? `#${r.ancla}` : ""));
    onCerrar();
  };

  return (
    <div className={styles.buscadorFondo} onClick={onCerrar}>
      <div
        className={styles.buscador}
        role="dialog"
        aria-modal="true"
        aria-label="Buscar en la guía"
        onClick={(e) => e.stopPropagation()}
      >
        <div className={styles.buscadorEntrada}>
          <Search size={18} aria-hidden="true" />
          <input
            ref={entrada}
            value={consulta}
            onChange={(e) => {
              setConsulta(e.target.value);
              setActivo(0);
            }}
            onKeyDown={(e) => {
              if (e.key === "Escape") onCerrar();
              else if (e.key === "ArrowDown") {
                e.preventDefault();
                setActivo((a) => Math.min(a + 1, resultados.length - 1));
              } else if (e.key === "ArrowUp") {
                e.preventDefault();
                setActivo((a) => Math.max(a - 1, 0));
              } else if (e.key === "Enter" && resultados[activo]) ir(resultados[activo]);
            }}
            placeholder="Buscar en la guía: factura, cama baja, prefijo…"
            aria-label="Texto a buscar"
            aria-controls="resultados-busqueda"
          />
          <kbd className={styles.kbd}>Esc</kbd>
        </div>
        <ul id="resultados-busqueda" className={styles.resultados} role="listbox" aria-label="Resultados">
          {consulta.trim().length >= 2 && resultados.length === 0 && (
            <li className={styles.sinResultados}>No encontramos «{consulta}» en la guía.</li>
          )}
          {resultados.map((r, i) => (
            <li key={r.pagina.ruta} role="option" aria-selected={i === activo}>
              <button
                type="button"
                className={[styles.resultado, i === activo ? styles.resultadoActivo : ""].join(" ")}
                onMouseEnter={() => setActivo(i)}
                onClick={() => ir(r)}
              >
                <span className={styles.resultadoRuta}>{tituloSeccion(r.pagina.seccion)}</span>
                <span className={styles.resultadoTitulo}>{r.pagina.titulo}</span>
                <span className={styles.resultadoFragmento}>{r.fragmento}</span>
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

// ── Menú lateral ─────────────────────────────────────────────────────────────

function MenuLateral({ actual, onNavegar }: { actual?: Pagina; onNavegar: () => void }) {
  return (
    <nav className={styles.menu} aria-label="Secciones de la guía">
      <Link to="/ayuda" className={styles.menuInicio} onClick={onNavegar}>
        <BookOpen size={16} aria-hidden="true" /> Inicio de la guía
      </Link>
      {SECCIONES.map((s) => {
        const paginas = paginasDeSeccion(s.slug);
        if (paginas.length === 0) return null;
        return (
          <div key={s.slug} className={styles.menuGrupo}>
            <div className={styles.menuGrupoTitulo}>{s.titulo}</div>
            {paginas.map((p) => {
              const esActual = actual?.ruta === p.ruta;
              return (
                <Link
                  key={p.ruta}
                  to={p.ruta}
                  onClick={onNavegar}
                  aria-current={esActual ? "page" : undefined}
                  className={[styles.menuItem, esActual ? styles.menuItemActivo : ""].join(" ")}
                >
                  {p.titulo}
                </Link>
              );
            })}
          </div>
        );
      })}
    </nav>
  );
}

// ── Índice "En esta página" ─────────────────────────────────────────────────

function EnEstaPagina({ pagina }: { pagina: Pagina }) {
  const [visible, setVisible] = useState<string | null>(null);
  useEffect(() => {
    const titulos = pagina.encabezados
      .map((e) => document.getElementById(e.id))
      .filter((x): x is HTMLElement => Boolean(x));
    const observador = new IntersectionObserver(
      (entradas) => {
        const arriba = entradas.filter((e) => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
        if (arriba) setVisible(arriba.target.id);
      },
      { rootMargin: "-80px 0px -65% 0px" },
    );
    titulos.forEach((t) => observador.observe(t));
    return () => observador.disconnect();
  }, [pagina]);

  if (pagina.encabezados.length === 0) return null;
  return (
    <nav className={styles.indice} aria-label="En esta página">
      <div className={styles.indiceTitulo}>En esta página</div>
      <ul>
        {pagina.encabezados.map((e) => (
          <li key={e.id} className={e.nivel === 3 ? styles.indiceSub : undefined}>
            <a href={`#${e.id}`} className={visible === e.id ? styles.indiceActivo : undefined}>
              {e.texto}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
}

// ── Páginas ──────────────────────────────────────────────────────────────────

function PaginaGuia() {
  const { seccion = "", pagina: slug } = useParams();
  const pagina = buscarPagina(seccion, slug);
  const location = useLocation();
  const bloques = useMemo(() => (pagina ? analizar(pagina.cuerpo) : []), [pagina]);

  useEffect(() => {
    if (!pagina) return;
    document.title = `${pagina.titulo} · Guía de usuario`;
    const id = decodeURIComponent(location.hash.slice(1));
    const destino = id ? document.getElementById(id) : null;
    if (destino) destino.scrollIntoView();
    else window.scrollTo(0, 0);
  }, [pagina, location.hash]);

  if (!pagina) return <Navigate to="/ayuda" replace />;
  if (!slug) return <Navigate to={pagina.ruta + location.hash} replace />;

  const i = PAGINAS.indexOf(pagina);
  const anterior = PAGINAS[i - 1];
  const siguiente = PAGINAS[i + 1];

  return (
    <div className={styles.paginaConIndice}>
      <article className={styles.articulo}>
        <nav className={styles.miga} aria-label="Ruta de navegación">
          <Link to="/ayuda">Guía de usuario</Link>
          <span aria-hidden="true">/</span>
          <Link to={`/ayuda/${pagina.seccion}`}>{tituloSeccion(pagina.seccion)}</Link>
          <span aria-hidden="true">/</span>
          <span aria-current="page">{pagina.titulo}</span>
        </nav>
        <h1 className={styles.titulo}>{pagina.titulo}</h1>
        {pagina.descripcion && <p className={styles.descripcion}>{pagina.descripcion}</p>}
        <div className={styles.meta}>
          {pagina.soloAdministrador && <span className={styles.etiquetaAdmin}>Solo administrador</span>}
          {pagina.actualizado && <span>Actualizado: {fechaLegible(pagina.actualizado)}</span>}
          <button type="button" className={styles.botonImprimir} onClick={() => window.print()}>
            <Printer size={15} aria-hidden="true" /> Imprimir esta página
          </button>
        </div>
        <div className={styles.brillo} aria-hidden="true" />
        <div className={styles.cuerpo}>
          <Contenido bloques={bloques} seccion={pagina.seccion} />
        </div>
        <nav className={styles.anteriorSiguiente} aria-label="Páginas anterior y siguiente">
          {anterior ? (
            <Link to={anterior.ruta} className={styles.navPagina}>
              <span className={styles.navEtiqueta}>
                <ArrowLeft size={14} aria-hidden="true" /> Anterior
              </span>
              <span>{anterior.titulo}</span>
            </Link>
          ) : (
            <span />
          )}
          {siguiente && (
            <Link to={siguiente.ruta} className={`${styles.navPagina} ${styles.navSiguiente}`}>
              <span className={styles.navEtiqueta}>
                Siguiente <ArrowRight size={14} aria-hidden="true" />
              </span>
              <span>{siguiente.titulo}</span>
            </Link>
          )}
        </nav>
      </article>
      <EnEstaPagina pagina={pagina} />
    </div>
  );
}

function PortadaGuia() {
  useEffect(() => {
    document.title = "Guía de usuario · Sistema de Remisiones";
  }, []);
  return (
    <article className={styles.articulo}>
      <h1 className={styles.titulo}>Guía de usuario</h1>
      <p className={styles.descripcion}>
        Cómo usar el Sistema de Remisiones paso a paso: remisiones, facturación, catálogos, reportes y administración.
        Usa el buscador (<kbd className={styles.kbd}>Ctrl</kbd> + <kbd className={styles.kbd}>K</kbd>) para encontrar un
        tema.
      </p>
      <div className={styles.brillo} aria-hidden="true" />
      <div className={styles.tarjetas}>
        {SECCIONES.map((s) => {
          const paginas = paginasDeSeccion(s.slug);
          if (paginas.length === 0) return null;
          return (
            <Link key={s.slug} to={paginas[0].ruta} className={styles.tarjeta}>
              <span className={styles.tarjetaTitulo}>{s.titulo}</span>
              <span className={styles.tarjetaTexto}>{paginas.map((p) => p.titulo).join(" · ")}</span>
            </Link>
          );
        })}
      </div>
    </article>
  );
}

// ── Marco general ────────────────────────────────────────────────────────────

export default function Guia() {
  const [buscando, setBuscando] = useState(false);
  const [menuAbierto, setMenuAbierto] = useState(false);
  const location = useLocation();
  const [, , seccion, slug] = location.pathname.split("/");
  const actual = seccion ? buscarPagina(seccion, slug) : undefined;

  useEffect(() => {
    const atajo = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setBuscando(true);
      } else if (e.key === "Escape") {
        // También cierra si el foco todavía no llegó al campo de búsqueda.
        setBuscando(false);
        setMenuAbierto(false);
      }
    };
    window.addEventListener("keydown", atajo);
    return () => window.removeEventListener("keydown", atajo);
  }, []);

  return (
    <div className={styles.guia}>
      <a href="#contenido-guia" className={styles.saltar}>
        Saltar al contenido
      </a>
      <header className={styles.barra}>
        <button
          type="button"
          className={styles.botonMenu}
          onClick={() => setMenuAbierto((v) => !v)}
          aria-expanded={menuAbierto}
          aria-controls="menu-guia"
          aria-label={menuAbierto ? "Cerrar menú de secciones" : "Abrir menú de secciones"}
        >
          {menuAbierto ? <X size={20} /> : <Menu size={20} />}
        </button>
        <Link to="/ayuda" className={styles.marca}>
          <span className={styles.marcaSistema}>Sistema de Remisiones</span>
          <span className={styles.marcaGuia}>Guía de usuario</span>
        </Link>
        <button type="button" className={styles.botonBuscar} onClick={() => setBuscando(true)}>
          <Search size={16} aria-hidden="true" />
          <span className={styles.botonBuscarTexto}>Buscar en la guía</span>
          <kbd className={styles.kbd}>Ctrl K</kbd>
        </button>
        <a href="/" className={styles.volver}>
          <ArrowLeft size={16} aria-hidden="true" />
          <span className={styles.volverTexto}>Volver a la aplicación</span>
        </a>
      </header>

      <div className={styles.cuerpoGuia}>
        <aside id="menu-guia" className={[styles.lateral, menuAbierto ? styles.lateralAbierto : ""].join(" ")}>
          <MenuLateral actual={actual} onNavegar={() => setMenuAbierto(false)} />
        </aside>
        {menuAbierto && <div className={styles.lateralFondo} onClick={() => setMenuAbierto(false)} aria-hidden="true" />}
        <main id="contenido-guia" className={styles.principal} tabIndex={-1}>
          <Routes>
            <Route index element={<PortadaGuia />} />
            <Route path=":seccion" element={<PaginaGuia />} />
            <Route path=":seccion/:pagina" element={<PaginaGuia />} />
            <Route path="*" element={<Navigate to="/ayuda" replace />} />
          </Routes>
          <footer className={styles.pie}>{TEXTO_DERECHOS}</footer>
        </main>
      </div>
      <Buscador abierto={buscando} onCerrar={() => setBuscando(false)} />
    </div>
  );
}
