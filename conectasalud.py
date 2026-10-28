import sqlite3
from datetime import datetime
from pathlib import Path

import streamlit as st

# Configuración
DB_PATH = Path(__file__).with_name("conectasalud.db")

ESTADOS = [
    "Disponible",
    "Aceptado",
    "Retirado en farmacia",
    "Entregado",
    "Cancelado"
]


# Base de datos
def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def inicializar_bd():
    with conectar() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente TEXT NOT NULL,
                farmacia TEXT NOT NULL,
                direccion TEXT NOT NULL,
                detalle TEXT NOT NULL,
                distancia REAL NOT NULL,
                pago REAL NOT NULL,
                notas TEXT DEFAULT '',
                estado TEXT NOT NULL DEFAULT 'Disponible',
                estudiante TEXT DEFAULT '',
                creado TEXT NOT NULL
            )
        """)


def crear_pedido(
    cliente, farmacia, direccion, detalle,
    distancia, pago, notas
):
    with conectar() as conn:
        conn.execute("""
            INSERT INTO pedidos (
                cliente, farmacia, direccion, detalle,
                distancia, pago, notas, estado, creado
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Disponible', ?)
        """, (
            cliente, farmacia, direccion, detalle,
            distancia, pago, notas,
            datetime.now().strftime("%d-%m-%Y %H:%M")
        ))


def obtener_pedidos(estado=None):
    with conectar() as conn:
        if estado:
            return conn.execute(
                """SELECT * FROM pedidos
                   WHERE estado = ?
                   ORDER BY id DESC""",
                (estado,)
            ).fetchall()

        return conn.execute(
            "SELECT * FROM pedidos ORDER BY id DESC"
        ).fetchall()


def actualizar_pedido(pedido_id, estado, estudiante=None):
    with conectar() as conn:
        if estudiante is not None:
            conn.execute("""
                UPDATE pedidos
                SET estado = ?, estudiante = ?
                WHERE id = ? AND estado = 'Disponible'
            """, (estado, estudiante, pedido_id))
        else:
            conn.execute("""
                UPDATE pedidos
                SET estado = ?
                WHERE id = ?
            """, (estado, pedido_id))


def dinero(valor):
    return "$" + f"{valor:,.0f}".replace(",", ".")


# Interfaz
st.set_page_config(
    page_title="ConectaSalud en Rueda",
    page_icon="🚲",
    layout="wide"
)

inicializar_bd()

st.title("🚲 ConectaSalud en Rueda")
st.write(
    "Una red comunitaria para acercar medicamentos "
    "a personas con movilidad reducida."
)

st.sidebar.title("Menú")

pagina = st.sidebar.radio(
    "Selecciona una sección",
    [
        "Inicio",
        "Solicitar un despacho",
        "Repartos en bicicleta",
        "Seguimiento",
        "Administración"
    ]
)

st.sidebar.info(
    "Prototipo educativo. Utiliza solamente "
    "datos ficticios."
)

todos = obtener_pedidos()

disponibles = [
    p for p in todos if p["estado"] == "Disponible"
]

activos = [
    p for p in todos
    if p["estado"] in [
        "Aceptado", "Retirado en farmacia"
    ]
]

entregados = [
    p for p in todos if p["estado"] == "Entregado"
]


# Inicio
if pagina == "Inicio":

    st.subheader("Estado de la plataforma")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Pedidos disponibles",
        len(disponibles)
    )

    col2.metric(
        "Entregas en curso",
        len(activos)
    )

    col3.metric(
        "Entregas completadas",
        len(entregados)
    )

    st.subheader("¿Cómo funciona?")

    st.markdown("""
    **1. Solicitud:** una persona registra un pedido.

    **2. Asignación:** un estudiante acepta el reparto
    en bicicleta.

    **3. Retiro:** el estudiante recoge el pedido
    en la farmacia.

    **4. Entrega:** se actualiza el estado cuando
    el pedido llega a su destino.
    """)

    st.info(
        "Esta versión simula la coordinación. "
        "No utiliza GPS ni envía notificaciones reales."
    )

    st.subheader("Pedidos recientes")

    if todos:
        for p in todos[:5]:
            with st.container(border=True):
                st.write(
                    f"**Pedido #{p['id']}** — {p['estado']}"
                )
                st.write(
                    f"{p['farmacia']} → {p['direccion']}"
                )
    else:
        st.write("Todavía no hay pedidos registrados.")


# Crear pedidos
elif pagina == "Solicitar un despacho":

    st.subheader("Solicitar un despacho")

    st.warning(
        "Usa nombres, direcciones y referencias ficticias. "
        "No introduzcas datos médicos personales."
    )

    with st.form("form_pedido"):

        cliente = st.text_input(
            "Nombre o código del solicitante"
        )

        farmacia = st.text_input(
            "Farmacia de retiro"
        )

        direccion = st.text_input(
            "Dirección de entrega ficticia"
        )

        detalle = st.text_input(
            "Referencia del pedido"
        )

        col1, col2 = st.columns(2)

        with col1:
            distancia = st.number_input(
                "Distancia estimada (km)",
                min_value=0.1,
                max_value=50.0,
                value=2.0,
                step=0.5
            )

        with col2:
            pago = st.number_input(
                "Pago al repartidor (CLP)",
                min_value=0,
                max_value=100000,
                value=2000,
                step=500
            )

        notas = st.text_area(
            "Indicaciones de entrega"
        )

        confirmar = st.checkbox(
            "Confirmo que usaré datos ficticios."
        )

        enviar = st.form_submit_button(
            "Crear pedido",
            type="primary"
        )

        if enviar:

            if not all([
                cliente.strip(),
                farmacia.strip(),
                direccion.strip(),
                detalle.strip()
            ]):
                st.error(
                    "Completa todos los campos obligatorios."
                )

            elif not confirmar:
                st.error(
                    "Confirma que utilizarás datos ficticios."
                )

            else:
                crear_pedido(
                    cliente.strip(),
                    farmacia.strip(),
                    direccion.strip(),
                    detalle.strip(),
                    distancia,
                    pago,
                    notas.strip()
                )

                st.success("Pedido creado correctamente.")
                st.rerun()


# Repartos
elif pagina == "Repartos en bicicleta":

    st.subheader("Pedidos disponibles")

    estudiante = st.text_input(
        "Nombre o código del estudiante",
        placeholder="Ej.: Estudiante 007"
    )

    if not disponibles:
        st.info("No hay pedidos disponibles.")

    for p in disponibles:

        with st.container(border=True):

            st.markdown(
                f"### Pedido #{p['id']}"
            )

            st.write(
                f"**Farmacia:** {p['farmacia']}"
            )

            st.write(
                f"**Destino:** {p['direccion']}"
            )

            st.write(
                f"**Referencia:** {p['detalle']}"
            )

            st.write(
                f"**Distancia:** {p['distancia']:.1f} km"
            )

            st.write(
                f"**Pago:** {dinero(p['pago'])}"
            )

            if p["notas"]:
                st.caption(p["notas"])

            if st.button(
                "Aceptar reparto",
                key=f"aceptar_{p['id']}"
            ):
                if not estudiante.strip():
                    st.error(
                        "Introduce tu nombre o código."
                    )
                else:
                    actualizar_pedido(
                        p["id"],
                        "Aceptado",
                        estudiante.strip()
                    )

                    st.success(
                        f"Pedido #{p['id']} asignado."
                    )

                    st.rerun()


# Seguimiento
elif pagina == "Seguimiento":

    st.subheader("Seguimiento de pedidos")

    filtro = st.selectbox(
        "Filtrar por estado",
        ["Todos"] + ESTADOS
    )

    pedidos = obtener_pedidos(
        None if filtro == "Todos" else filtro
    )

    if not pedidos:
        st.info("No hay pedidos para mostrar.")

    for p in pedidos:

        with st.container(border=True):

            st.markdown(
                f"### Pedido #{p['id']} — {p['estado']}"
            )

            st.write(
                f"**Ruta:** {p['farmacia']} → {p['direccion']}"
            )

            st.write(
                f"**Solicitante:** {p['cliente']}"
            )

            st.write(
                f"**Estudiante:** "
                f"{p['estudiante'] or 'Sin asignar'}"
            )

            st.write(
                f"**Distancia:** {p['distancia']:.1f} km"
            )

            st.write(
                f"**Pago:** {dinero(p['pago'])}"
            )

            st.caption(f"Creado: {p['creado']}")


# Administración
elif pagina == "Administración":

    st.subheader("Administración de pedidos")

    pedidos = obtener_pedidos()

    if not pedidos:
        st.info("No hay pedidos registrados.")

    else:
        opciones = {
            f"Pedido #{p['id']} — {p['estado']}": p
            for p in pedidos
        }

        seleccionado = st.selectbox(
            "Seleccionar pedido",
            list(opciones.keys())
        )

        pedido = opciones[seleccionado]

        nuevo_estado = st.selectbox(
            "Nuevo estado",
            ESTADOS,
            index=ESTADOS.index(pedido["estado"])
        )

        if st.button(
            "Guardar cambios",
            type="primary"
        ):
            actualizar_pedido(
                pedido["id"],
                nuevo_estado
            )

            st.success("Estado actualizado.")
            st.rerun()

    st.divider()

    st.caption(
        "Los pedidos se guardan en el archivo "
        "conectasalud.db, ubicado junto al programa."
    )