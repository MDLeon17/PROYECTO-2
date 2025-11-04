from __future__ import annotations

import os
import smtplib
import sys
from contextlib import contextmanager
from datetime import date, datetime
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, Iterator, Optional, Tuple

import psycopg2
from psycopg2 import errors
from psycopg2.extensions import connection
from tkcalendar import Calendar
from tkinter import messagebox, ttk
import tkinter as tk
from PIL import Image, ImageTk


###############################################################################
# Configuration
###############################################################################


def _env_or_default(name: str, default: str) -> str:
    """Return the environment variable value when available."""

    return os.environ.get(name, default)


PG_CONFIG = {
    "host": _env_or_default("PGHOST", "ep-lucky-hill-ad6ietmz-pooler.c-2.us-east-1.aws.neon.tech"),
    "dbname": _env_or_default("PGDATABASE", "neondb"),
    "user": _env_or_default("PGUSER", "neondb_owner"),
    "password": _env_or_default("PGPASSWORD", "npg_xcUk0eiJLI1F"),
    "sslmode": _env_or_default("PGSSLMODE", "require"),
}

GMAIL_ACCOUNT = _env_or_default("GMAIL_ACCOUNT", "fnandomendezdleon@gmail.com")
GMAIL_APP_PASSWORD = _env_or_default("GMAIL_APP_PASSWORD", "ggvv ackz yvwm gjys")
SMTP_SERVER = _env_or_default("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(_env_or_default("SMTP_PORT", "587"))

HORAS_LABORALES: Tuple[str, ...] = (
    "14:15",
    "15:15",
    "16:15",
    "17:15",
    "18:15",
)

USERS: Dict[str, Tuple[str, str]] = {
    "admin": (
        _env_or_default("ADMIN_PASSWORD", "admin123"),
        "Administrador",
    ),
    "doctor": (
        _env_or_default("DOCTOR_PASSWORD", "doctor123"),
        "Doctor",
    ),
}


###############################################################################
# Helpers
###############################################################################


def resource_path(relative_path: str) -> str:
    """Return an absolute path for resources bundled with PyInstaller."""

    candidatos = []

    try:
        candidatos.append(Path(sys._MEIPASS) / relative_path)  # type: ignore[attr-defined]
    except AttributeError:
        pass

    candidatos.append(Path.cwd() / relative_path)
    candidatos.append(Path(__file__).resolve().parent / relative_path)

    for ruta in candidatos:
        if ruta.exists():
            return str(ruta)

    return str(candidatos[-1])


@contextmanager
def get_conn() -> Iterator[connection]:
    """Context manager that yields a PostgreSQL connection."""

    conn = psycopg2.connect(**PG_CONFIG)
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    """Create the schema when tables do not exist."""

    try:
        with get_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS pacientes (
                        id      SERIAL PRIMARY KEY,
                        nombre  TEXT NOT NULL,
                        correo  TEXT NOT NULL,
                        edad    INTEGER,
                        dpi     TEXT UNIQUE
                    );
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS citas_medicas (
                        id          SERIAL PRIMARY KEY,
                        paciente_id INTEGER NOT NULL REFERENCES pacientes(id) ON DELETE CASCADE ON UPDATE CASCADE,
                        fecha       DATE NOT NULL,
                        hora        TIME NOT NULL,
                        motivo      TEXT NOT NULL,
                        codigo_cita TEXT UNIQUE,
                        estado      TEXT DEFAULT 'PROGRAMADA',
                        creado_en   TIMESTAMP DEFAULT NOW()
                    );
                    """
                )
            conn.commit()
    except Exception as exc:  # pragma: no cover - GUI feedback only
        messagebox.showerror("Error de BD", f"No se pudo inicializar la BD:\n{exc}")


###############################################################################
# Pacientes
###############################################################################


def agregar_pacientes(padre: Optional[tk.Misc]) -> None:
    """Open the dialog that creates a new patient."""

    ventana = tk.Toplevel(padre)
    ventana.geometry("900x600")
    ventana.config(bg="#0b1220")
    ventana.title("AGREGAR PACIENTES")

    campos = {
        "nombre": tk.Entry(ventana),
        "edad": tk.Entry(ventana),
        "dpi": tk.Entry(ventana),
        "correo": tk.Entry(ventana),
    }

    etiquetas = {
        "nombre": "NOMBRE DEL PACIENTE  :",
        "edad": "EDAD DEL PACIENTE  :",
        "dpi": "DPI/CUI DEL PACIENTE  :",
        "correo": "CORREO DEL PACIENTE  :",
    }

    for index, (clave, label_text) in enumerate(etiquetas.items()):
        tk.Label(ventana, text=label_text, bg="#0b1220", fg="#CAF0F8").place(x=20, y=50 + 100 * index)
        campos[clave].place(x=200, y=50 + 100 * index, height=30, width=600)

    def limpiar_campos() -> None:
        for entry in campos.values():
            entry.delete(0, tk.END)

    def validar_datos() -> Optional[Tuple[str, int, str, str]]:
        nombre = campos["nombre"].get().strip().upper()
        edad = campos["edad"].get().strip()
        dpi = campos["dpi"].get().strip().upper()
        correo = campos["correo"].get().strip()

        if not all((nombre, edad, dpi, correo)):
            messagebox.showwarning("Campos vacíos", "Por favor, complete todos los campos.")
            return None
        if "@" not in correo or "." not in correo:
            messagebox.showwarning("Correo inválido", "Por favor, ingrese un correo válido.")
            return None
        try:
            edad_int = int(edad)
        except ValueError:
            messagebox.showwarning("Edad inválida", "Por favor, ingrese una edad numérica.")
            return None
        if edad_int < 0 or edad_int > 120:
            messagebox.showwarning("Edad inválida", "Por favor, ingrese una edad válida.")
            return None
        return nombre, edad_int, dpi, correo

    def guardar() -> None:
        datos = validar_datos()
        if not datos:
            return
        nombre, edad_int, dpi, correo = datos

        if not messagebox.askyesno(
            "CONFIRMACION",
            "¿DESEA AGREGAR AL SIGUIENTE PACIENTE?\n\n"
            f"NOMBRE: {nombre}\nEDAD: {edad_int}\nDPI/CUI: {dpi}\nCORREO: {correo}",
        ):
            return

        try:
            with get_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO pacientes (nombre, correo, edad, dpi) VALUES (%s, %s, %s, %s)",
                        (nombre, correo, edad_int, dpi),
                    )
                conn.commit()
            messagebox.showinfo("ÉXITO", "PACIENTE AGREGADO EXITOSAMENTE")
            limpiar_campos()
        except errors.UniqueViolation:
            messagebox.showerror("Error de BD", "El DPI ya existe (UNIQUE).")
        except Exception as exc:
            messagebox.showerror("Error inesperado", str(exc))

    tk.Button(
        ventana,
        text="GUARDAR PACIENTE",
        fg="#023E8A",
        bg="#CAF0F8",
        command=guardar,
    ).place(x=350, y=450, height=40, width=200)


def borrar_paciente() -> None:
    ventana = tk.Toplevel()
    ventana.geometry("325x400")
    ventana.title("Borrar Pacientes")
    ventana.config(bg="#0b1220")

    tk.Label(
        ventana,
        text="INTRODUZCA EL DPI DEL PACIENTE A BORRAR",
        bg="#0b1220",
        fg="#CAF0F8",
    ).place(x=20, y=20)

    entry_dpi = tk.Entry(ventana)
    entry_dpi.place(x=20, y=50, width=280)

    resultado_text = tk.Text(ventana, width=35, height=8, bg="#0b1220", fg="#CAF0F8")
    resultado_text.place(x=20, y=100)

    def borrar() -> None:
        dpi = entry_dpi.get().strip().upper()
        if not dpi:
            messagebox.showwarning("FALTA INGRESAR DPI", "Ingrese DPI")
            return
        try:
            with get_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id, nombre FROM pacientes WHERE dpi = %s", (dpi,))
                    fila = cursor.fetchone()
                    if not fila:
                        messagebox.showinfo(
                            "ERROR", "No se ha encontrado usuario con ese DPI, intente de nuevo"
                        )
                        return

                    resultado_text.delete("1.0", tk.END)
                    resultado_text.insert(
                        tk.END, f"Paciente encontrado:\nID: {fila[0]} | Nombre: {fila[1]}\n"
                    )

                    if not messagebox.askyesno(
                        "Confirmar borrado",
                        f"¿Seguro que quieres eliminar al paciente '{fila[1]}' con DPI {dpi}?",
                    ):
                        return

                    cursor.execute("DELETE FROM pacientes WHERE dpi = %s", (dpi,))
                conn.commit()

            messagebox.showinfo("USUARIO BORRADO", f"Paciente con DPI {dpi} eliminado")
            resultado_text.insert(tk.END, "CLIENTE ELIMINADO")
        except Exception as exc:
            messagebox.showerror("Error de BD", f"Error de base de datos:\n{exc}")

    tk.Button(
        ventana,
        text="BORRAR",
        fg="#023E8A",
        bg="#CAF0F8",
        command=borrar,
    ).place(x=20, y=250, width=280, height=30)


###############################################################################
# Email
###############################################################################


def mandar_email() -> None:
    ventana = tk.Toplevel()
    ventana.config(bg="#0b1220")
    ventana.geometry("650x600")
    ventana.title("ENVIAR CORREO")

    tk.Label(ventana, text="CORREO PACIENTE", bg="#0b1220", fg="#CAF0F8").place(x=20, y=20)
    tk.Label(ventana, text="ASUNTO CORREO", bg="#0b1220", fg="#CAF0F8").place(x=20, y=75)
    tk.Label(ventana, text="CUERPO CORREO", bg="#0b1220", fg="#CAF0F8").place(x=20, y=150)

    entry_correo = tk.Entry(ventana)
    entry_titulo = tk.Entry(ventana)
    entry_cuerpo = tk.Text(ventana, bg="#0b1220", fg="#CAF0F8")

    entry_correo.place(x=150, y=20, width=300)
    entry_titulo.place(x=150, y=75, width=300)
    entry_cuerpo.place(x=20, y=175, width=600, height=300)

    def email() -> None:
        cuerpo = entry_cuerpo.get("1.0", tk.END).strip()
        asunto = entry_titulo.get().strip()
        correo_destino = entry_correo.get().strip()

        if not cuerpo:
            messagebox.showerror("ERROR", "EL CUERPO DEL CORREO NO PUEDE ESTAR VACIO")
            return
        if "@" not in correo_destino:
            messagebox.showerror("ERROR", "CORREO INVALIDO")
            return
        if not asunto:
            messagebox.showerror("ERROR", "NECESITAS PONERLE UN TITULO")
            return

        mensaje = MIMEText(cuerpo)
        mensaje["From"] = GMAIL_ACCOUNT
        mensaje["To"] = correo_destino
        mensaje["Subject"] = asunto

        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(GMAIL_ACCOUNT, GMAIL_APP_PASSWORD)
                server.sendmail(GMAIL_ACCOUNT, correo_destino, mensaje.as_string())
            messagebox.showinfo("CORREO", "Correo enviado con éxito.")
        except Exception as exc:
            messagebox.showerror("Error", f"Error al enviar el correo:\n{exc}")

    tk.Button(
        ventana,
        text="Enviar correo",
        command=email,
        height=5,
        width=84,
        fg="#023E8A",
        bg="#CAF0F8",
    ).place(x=20, y=500)


###############################################################################
# Citas
###############################################################################


def agendar_cita_nueva() -> None:
    ventana = tk.Toplevel()
    ventana.title("Agendar Nueva Cita")
    ventana.geometry("750x550")
    ventana.config(bg="#0b1220")

    paciente_map: Dict[str, int] = {}

    frame_izquierdo = tk.Frame(ventana, bg="#0b1220", width=400, height=500)
    frame_derecho = tk.Frame(ventana, bg="#0b1220", width=300, height=500)

    frame_izquierdo.pack(side="left", fill="y", padx=20, pady=20)
    frame_derecho.pack(side="right", fill="both", expand=True, padx=20, pady=20)
    frame_izquierdo.pack_propagate(False)

    tk.Label(
        frame_izquierdo,
        text="1. Seleccione el Día",
        bg="#0b1220",
        fg="#CAF0F8",
        font=("Arial", 14),
    ).pack(pady=(0, 10))
    cal = Calendar(
        frame_izquierdo,
        selectmode="day",
        mindate=date.today(),
        background="#023E8A",
        foreground="white",
        headersbackground="#0077B6",
        normalbackground="#90E0EF",
        weekendbackground="#48CAE4",
    )
    cal.pack(fill="x", expand=True)

    tk.Label(
        frame_derecho,
        text="2. Seleccione el Paciente",
        bg="#0b1220",
        fg="#CAF0F8",
        font=("Arial", 14),
    ).pack(pady=(10, 10), anchor="w")

    frame_paciente = tk.Frame(frame_derecho, bg="#0b1220")
    frame_paciente.pack(fill="x", pady=5)

    combo_pacientes = ttk.Combobox(frame_paciente, state="readonly", width=35, font=("Arial", 12))
    combo_pacientes.pack(side="left", fill="x", expand=True)

    btn_agregar_pac = tk.Button(
        frame_paciente,
        text="+",
        font=("Arial", 14, "bold"),
        fg="#023E8A",
        bg="#CAF0F8",
        width=3,
    )
    btn_agregar_pac.pack(side="right", padx=(10, 0))

    tk.Label(
        frame_derecho,
        text="3. Seleccione la Hora Disponible",
        bg="#0b1220",
        fg="#CAF0F8",
        font=("Arial", 14),
    ).pack(pady=(20, 10), anchor="w")

    frame_horas = tk.Frame(frame_derecho)
    frame_horas.pack(fill="both", expand=True)

    horas_listbox = tk.Listbox(
        frame_horas,
        selectmode=tk.SINGLE,
        font=("Arial", 12),
        height=10,
        bg="#0b1220",
        fg="#CAF0F8",
        selectbackground="#0077B6",
        selectforeground="white",
    )

    sb_horas = ttk.Scrollbar(frame_horas, orient="vertical", command=horas_listbox.yview)
    horas_listbox.configure(yscrollcommand=sb_horas.set)

    sb_horas.pack(side="right", fill="y")
    horas_listbox.pack(side="left", fill="both", expand=True)

    def cargar_pacientes_combobox() -> None:
        paciente_map.clear()
        try:
            with get_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id, nombre FROM pacientes ORDER BY nombre ASC")
                    pacientes_db = cursor.fetchall()
        except Exception as exc:
            messagebox.showerror("Error DB", f"No se pudieron cargar pacientes:\n{exc}", parent=ventana)
            return

        nombres = [nombre for _, nombre in pacientes_db]
        for pac_id, nombre in pacientes_db:
            paciente_map[nombre] = pac_id

        combo_pacientes["values"] = nombres or ("No hay pacientes registrados",)
        if nombres:
            combo_pacientes.set(nombres[0])
        else:
            combo_pacientes.set("No hay pacientes registrados")

    def actualizar_horas_disponibles(event: Optional[tk.Event] = None) -> None:  # noqa: ARG001
        horas_listbox.delete(0, tk.END)

        try:
            fecha_seleccionada = datetime.strptime(cal.get_date(), "%m/%d/%y")
        except Exception as exc:
            messagebox.showerror("Error de fecha", f"No se pudo leer la fecha: {exc}", parent=ventana)
            return

        fecha_sql = fecha_seleccionada.strftime("%Y-%m-%d")

        try:
            with get_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT hora FROM citas_medicas WHERE fecha = %s", (fecha_sql,))
                    horas_ocupadas = {row[0].strftime("%H:%M") for row in cursor.fetchall()}
        except Exception as exc:
            messagebox.showerror("Error DB", f"No se pudieron cargar las horas:\n{exc}", parent=ventana)
            return

        horas_disponibles = [hora for hora in HORAS_LABORALES if hora not in horas_ocupadas]
        if not horas_disponibles:
            horas_listbox.insert(tk.END, "No hay horas disponibles")
        else:
            for hora in horas_disponibles:
                horas_listbox.insert(tk.END, hora)

    def abrir_ventana_agregar_paciente() -> None:
        agregar_pacientes(ventana)
        cargar_pacientes_combobox()

    def guardar_nueva_cita() -> None:
        nombre_paciente = combo_pacientes.get()
        if not nombre_paciente or nombre_paciente not in paciente_map:
            messagebox.showwarning(
                "Paciente no válido", "Por favor, seleccione un paciente de la lista.", parent=ventana
            )
            return

        paciente_id = paciente_map[nombre_paciente]

        try:
            hora_seleccionada = horas_listbox.get(horas_listbox.curselection())
            if ":" not in hora_seleccionada:
                raise ValueError
        except (tk.TclError, ValueError, IndexError):
            messagebox.showwarning(
                "Hora no válida", "Por favor, seleccione una hora disponible de la lista.", parent=ventana
            )
            return

        fecha_sel = datetime.strptime(cal.get_date(), "%m/%d/%y")
        fecha_sql = fecha_sel.strftime("%Y-%m-%d")

        codigo_cita = f"{nombre_paciente.strip().upper()[:3]}{fecha_sel.day:02d}"

        if not messagebox.askyesno(
            "Confirmar Cita",
            "¿Desea agendar la cita?\n\n"
            f"Paciente: {nombre_paciente}\n"
            f"Fecha: {fecha_sql}\n"
            f"Hora: {hora_seleccionada}\n"
            f"Código: {codigo_cita}",
            parent=ventana,
        ):
            return

        try:
            with get_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO citas_medicas (paciente_id, fecha, hora, motivo, codigo_cita)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (paciente_id, fecha_sql, hora_seleccionada, "Cita de terapia", codigo_cita),
                    )
                conn.commit()
            messagebox.showinfo("Éxito", f"Cita agendada correctamente.\nCódigo: {codigo_cita}", parent=ventana)
            actualizar_horas_disponibles()
            combo_pacientes.set("")
        except errors.UniqueViolation:
            messagebox.showerror(
                "Error Cita",
                f"El código de cita '{codigo_cita}' ya existe para otra cita.",
                parent=ventana,
            )
        except Exception as exc:
            messagebox.showerror("Error de BD", f"Ocurrió un error al guardar:\n{exc}", parent=ventana)

    cal.bind("<<CalendarSelected>>", actualizar_horas_disponibles)
    btn_agregar_pac.config(command=abrir_ventana_agregar_paciente)

    tk.Button(
        frame_derecho,
        text="GUARDAR CITA",
        command=guardar_nueva_cita,
        bg="#CAF0F8",
        fg="#023E8A",
        font=("Arial", 12, "bold"),
        height=2,
    ).pack(side="bottom", fill="x", pady=(20, 0))

    cargar_pacientes_combobox()
    actualizar_horas_disponibles()


###############################################################################
# Pacientes listado y detalle
###############################################################################


def ventana_pacientes() -> None:
    ventana = tk.Toplevel()
    ventana.title("PACIENTES")
    ventana.geometry("750x520")
    ventana.config(bg="#0b1220")

    tk.Label(
        ventana,
        text="LISTA DE PACIENTES",
        font=("Arial", 14, "bold"),
        bg="#0b1220",
        fg="#CAF0F8",
    ).pack(pady=(10, 0))

    barra = tk.Frame(ventana, bg="#0b1220")
    barra.pack(fill="x", padx=10, pady=10)

    tk.Label(barra, text="Ordenar por:", bg="#0b1220", fg="#CAF0F8").pack(side="left", padx=(0, 8))

    sort_var = tk.StringVar(value="A → Z (Nombre)")
    combo_sort = ttk.Combobox(
        barra,
        textvariable=sort_var,
        state="readonly",
        values=["A → Z (Nombre)", "Z → A (Nombre)"],
    )
    combo_sort.pack(side="left")

    def abrir_agregar() -> None:
        agregar_pacientes(ventana)
        cargar_pacientes()

    tk.Button(
        barra,
        text="+",
        font=("Arial", 16, "bold"),
        fg="#023E8A",
        bg="#CAF0F8",
        command=abrir_agregar,
    ).pack(side="right", ipadx=10)

    cont_tabla = tk.Frame(ventana, bg="#0b1220")
    cont_tabla.pack(expand=True, fill="both", padx=10, pady=(0, 10))

    columns = ("id", "nombre", "correo", "edad", "dpi")
    tree = ttk.Treeview(cont_tabla, columns=columns, show="headings", height=16)
    vsb = ttk.Scrollbar(cont_tabla, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)

    for col in columns:
        tree.heading(col, text=col.upper())
        tree.column(col, width=130, anchor="center")
    tree.column("nombre", width=200, anchor="w")

    tree.pack(side="left", expand=True, fill="both")
    vsb.pack(side="right", fill="y")

    def limpiar_tree() -> None:
        for item in tree.get_children():
            tree.delete(item)

    def orden_sql() -> str:
        return "ASC" if "A → Z" in sort_var.get() else "DESC"

    def cargar_pacientes() -> None:
        limpiar_tree()
        try:
            with get_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        f"""
                        SELECT id, nombre, correo, edad, dpi
                        FROM pacientes
                        ORDER BY LOWER(nombre) {orden_sql()}, dpi {orden_sql()};
                        """
                    )
                    for row in cursor.fetchall():
                        tree.insert("", tk.END, values=row)
        except Exception as exc:
            messagebox.showerror("Error DB", f"No se pudo cargar pacientes:\n{exc}")

    def on_cambio_orden(_event: Optional[tk.Event] = None) -> None:
        cargar_pacientes()

    combo_sort.bind("<<ComboboxSelected>>", on_cambio_orden)

    def abrir_detalle(_event: tk.Event) -> None:
        seleccion = tree.selection()
        if not seleccion:
            return
        paciente = tree.item(seleccion)["values"]
        abrir_detalle_paciente(tuple(paciente))

    tree.bind("<Double-1>", abrir_detalle)
    cargar_pacientes()


def abrir_detalle_paciente(paciente: Tuple[int, str, str, Optional[int], str]) -> None:
    paciente_id, nombre, correo, edad, dpi = paciente

    ventana = tk.Toplevel()
    ventana.title(f"Detalle paciente: {nombre}")
    ventana.geometry("500x500")
    ventana.config(bg="#0b1220")

    tk.Label(ventana, text="NOMBRE:", bg="#0b1220", fg="#CAF0F8").place(x=20, y=20)
    entry_nombre = tk.Entry(ventana)
    entry_nombre.place(x=150, y=20, width=300)
    entry_nombre.insert(0, nombre)

    tk.Label(ventana, text="CORREO:", bg="#0b1220", fg="#CAF0F8").place(x=20, y=70)
    entry_correo = tk.Entry(ventana)
    entry_correo.place(x=150, y=70, width=300)
    entry_correo.insert(0, correo)

    tk.Label(ventana, text="DPI:", bg="#0b1220", fg="#CAF0F8").place(x=20, y=120)
    entry_dpi = tk.Entry(ventana)
    entry_dpi.place(x=150, y=120, width=300)
    entry_dpi.insert(0, dpi)

    tk.Label(ventana, text=f"EDAD: {edad}", bg="#0b1220", fg="#CAF0F8").place(x=20, y=170)

    def guardar_cambios() -> None:
        nuevo_nombre = entry_nombre.get().strip()
        nuevo_correo = entry_correo.get().strip()
        nuevo_dpi = entry_dpi.get().strip().upper()

        if not nuevo_nombre or not nuevo_correo or not nuevo_dpi:
            messagebox.showwarning("Campos vacíos", "Todos los campos son obligatorios")
            return
        try:
            with get_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "UPDATE pacientes SET nombre=%s, correo=%s, dpi=%s WHERE id=%s",
                        (nuevo_nombre, nuevo_correo, nuevo_dpi, paciente_id),
                    )
                conn.commit()
            messagebox.showinfo("Éxito", "Paciente actualizado correctamente")
            ventana.destroy()
        except Exception as exc:
            messagebox.showerror("Error DB", f"No se pudo actualizar:\n{exc}")

    tk.Button(
        ventana,
        text="GUARDAR CAMBIOS",
        fg="#023E8A",
        bg="#CAF0F8",
        command=guardar_cambios,
    ).place(x=150, y=220, width=200, height=40)


###############################################################################
# Calendario
###############################################################################


def ver_calendario() -> None:
    ventana = tk.Toplevel()
    ventana.title("Calendario de Citas")
    ventana.geometry("700x600")
    ventana.config(bg="#0b1220")

    frame_cal = tk.Frame(ventana, bg="#0b1220")
    frame_cal.pack(pady=10, padx=10, fill="x")

    cal = Calendar(
        frame_cal,
        selectmode="day",
        background="#023E8A",
        foreground="white",
        headersbackground="#0077B6",
        normalbackground="#90E0EF",
        weekendbackground="#48CAE4",
    )
    cal.pack(fill="x", expand=True)

    frame_citas = tk.Frame(ventana, bg="#0b1220")
    frame_citas.pack(pady=10, padx=10, fill="both", expand=True)

    tk.Label(
        frame_citas,
        text="Citas para el día seleccionado:",
        bg="#0b1220",
        fg="#CAF0F8",
        font=("Arial", 12),
    ).pack(anchor="w", pady=(0, 5))

    columns = ("hora", "paciente")
    tree = ttk.Treeview(frame_citas, columns=columns, show="headings", height=10)
    tree.heading("hora", text="Hora")
    tree.heading("paciente", text="Paciente")
    tree.column("hora", width=100, anchor="center")
    tree.column("paciente", width=350, anchor="w")

    vsb = ttk.Scrollbar(frame_citas, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)

    vsb.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)

    def cargar_citas_del_dia(_event: Optional[tk.Event] = None) -> None:
        for item in tree.get_children():
            tree.delete(item)

        try:
            fecha_sel = datetime.strptime(cal.get_date(), "%m/%d/%y")
        except Exception as exc:
            messagebox.showerror("Error de fecha", f"No se pudo leer la fecha: {exc}", parent=ventana)
            return

        fecha_sql = fecha_sel.strftime("%Y-%m-%d")

        try:
            with get_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT c.hora, p.nombre
                        FROM citas_medicas c
                        JOIN pacientes p ON c.paciente_id = p.id
                        WHERE c.fecha = %s
                        ORDER BY c.hora;
                        """,
                        (fecha_sql,),
                    )
                    citas = cursor.fetchall()
        except Exception as exc:
            messagebox.showerror("Error de BD", f"No se pudo cargar las citas:\n{exc}", parent=ventana)
            return

        if not citas:
            tree.insert("", tk.END, values=("", "No hay citas programadas"))
        else:
            for hora, paciente in citas:
                tree.insert("", tk.END, values=(hora.strftime("%H:%M"), paciente))

    cal.bind("<<CalendarSelected>>", cargar_citas_del_dia)
    cargar_citas_del_dia()


###############################################################################
# Menú principal
###############################################################################


def menu_principal(usuario: str, rol: str) -> None:
    global ventana_principal  # noqa: PLW0603

    try:
        ventana_principal.destroy()
    except Exception:
        pass

    ventana_principal = tk.Tk()
    ventana_principal.title("MENÚ PRINCIPAL")
    ventana_principal.geometry("400x600")
    ventana_principal.config(bg="#0b1220")

    imagen_path = Path(resource_path("logo_proyecto.png"))
    max_w, max_h = 300, 250

    if imagen_path.exists():
        try:
            img_original = Image.open(imagen_path)
            ratio = min(max_w / img_original.width, max_h / img_original.height, 1.0)
            new_w = int(img_original.width * ratio)
            new_h = int(img_original.height * ratio)
            img_redimensionada = img_original.resize((new_w, new_h), Image.LANCZOS)
            imagen = ImageTk.PhotoImage(img_redimensionada)

            imagen_label = tk.Label(ventana_principal, image=imagen, bg="#0b1220", bd=0)
            imagen_label.image = imagen
            x_pos = (400 - new_w) // 2
            y_pos = 600 - new_h - 20
            imagen_label.place(x=x_pos, y=y_pos)
        except Exception as exc:
            messagebox.showwarning("Logo", f"No se pudo cargar el logo:\n{exc}")
    else:
        messagebox.showwarning("Logo", "No se encontró el archivo del logo.")

    tk.Label(
        ventana_principal,
        text="MENÚ PRINCIPAL",
        font=("Arial", 18, "bold"),
        bg="#0b1220",
        fg="#CAF0F8",
    ).pack(pady=20)

    tk.Label(
        ventana_principal,
        text=f"Bienvenido, {usuario} ({rol})",
        font=("Arial", 12),
        bg="#0b1220",
        fg="#CAF0F8",
    ).pack(pady=(0, 20))

    botones = [
        ("PACIENTES", ventana_pacientes),
        ("CALENDARIO", ver_calendario),
        ("AGENDAR CITA", agendar_cita_nueva),
        ("ENVIAR CORREO", mandar_email),
    ]
    for texto, comando in botones:
        tk.Button(
            ventana_principal,
            text=texto,
            fg="#023E8A",
            bg="#CAF0F8",
            width=25,
            height=2,
            command=comando,
        ).pack(pady=10)

    ventana_principal.mainloop()


def ventana_login() -> None:
    login = tk.Tk()
    login.title("Iniciar sesión")
    login.geometry("350x250")
    login.config(bg="#0b1220")

    tk.Label(
        login,
        text="Seleccione usuario",
        font=("Arial", 12, "bold"),
        bg="#0b1220",
        fg="#CAF0F8",
    ).pack(pady=(20, 10))

    frame_form = tk.Frame(login, bg="#0b1220")
    frame_form.pack(pady=10)

    tk.Label(frame_form, text="Usuario", bg="#0b1220", fg="#CAF0F8").grid(row=0, column=0, sticky="e", padx=5, pady=5)
    tk.Label(frame_form, text="Contraseña", bg="#0b1220", fg="#CAF0F8").grid(row=1, column=0, sticky="e", padx=5, pady=5)

    usuario_var = tk.StringVar(value="admin")
    entry_usuario = ttk.Combobox(frame_form, textvariable=usuario_var, state="readonly", values=list(USERS.keys()))
    entry_usuario.grid(row=0, column=1, padx=5, pady=5)

    password_var = tk.StringVar()
    entry_password = tk.Entry(frame_form, textvariable=password_var, show="*")
    entry_password.grid(row=1, column=1, padx=5, pady=5)

    mensaje_estado = tk.Label(login, text="", bg="#0b1220", fg="#CAF0F8")
    mensaje_estado.pack(pady=(5, 0))

    def intentar_ingreso(_event: Optional[tk.Event] = None) -> None:
        usuario = usuario_var.get().strip().lower()
        password = password_var.get().strip()
        datos = USERS.get(usuario)
        if not datos or password != datos[0]:
            mensaje_estado.config(text="Credenciales inválidas", fg="#FF6B6B")
            return
        mensaje_estado.config(text="Acceso concedido", fg="#90E0EF")
        login.after(300, lambda: (login.destroy(), menu_principal(usuario.title(), datos[1])))

    tk.Button(
        login,
        text="Ingresar",
        fg="#023E8A",
        bg="#CAF0F8",
        width=15,
        command=intentar_ingreso,
    ).pack(pady=20)

    login.bind("<Return>", intentar_ingreso)
    entry_password.focus_set()
    login.mainloop()


###############################################################################
# Script entrypoint
###############################################################################


if __name__ == "__main__":
    init_db()
    ventana_login()