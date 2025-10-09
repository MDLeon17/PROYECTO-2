import tkinter as tk
from tkinter import messagebox
import psycopg2
from psycopg2 import sql, errors
import smtplib
from email.mime.text import MIMEText

PG_CONFIG = {
    "host": "ep-lucky-hill-ad6ietmz-pooler.c-2.us-east-1.aws.neon.tech",
    "dbname": "neondb",
    "user": "neondb_owner",
    "password": "npg_xcUk0eiJLI1F",
    "sslmode": "require"
}

#   EMAIL_SETTINGS
correo_persona = "fnandomendezdleon@gmail.com"
contraseña_personal = "ggvv ackz yvwm gjys"
smtpserver = "smtp.gmail.com"
puerto = 587


def get_conn():
    return psycopg2.connect(**PG_CONFIG)

# ========= INIT DB (CREATE TABLES) =========
def init_db():
    try:
        con = get_conn()
        cur = con.cursor()
        # Pacientes
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pacientes (
                id      SERIAL PRIMARY KEY,
                nombre  TEXT NOT NULL,
                estado  TEXT NOT NULL,
                edad    INTEGER,
                dpi     TEXT UNIQUE
            );
        """)
        # Citas (sin doctor)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS citas_medicas (
                id          SERIAL PRIMARY KEY,
                paciente_id INTEGER NOT NULL REFERENCES pacientes(id) ON DELETE CASCADE ON UPDATE CASCADE,
                fecha       DATE NOT NULL,
                hora        TIME NOT NULL,
                motivo      TEXT NOT NULL,
                estado      TEXT DEFAULT 'PROGRAMADA',
                creado_en   TIMESTAMP DEFAULT NOW()
            );
        """)
        con.commit()
        con.close()
    except Exception as e:
        messagebox.showerror("Error de BD", f"No se pudo inicializar la BD:\n{e}")

# ========= UI: Buscar por DPI (nueva ventana) =========
def buscar_cliente():
    ventana3 = tk.Toplevel(ventana1)
    ventana3.title("Buscar paciente por DPI")
    ventana3.geometry("600x320")
    ventana3.config(bg="black")
    ventana3.transient(ventana1)

    tk.Label(ventana3, text="Ingrese el DPI del paciente:", fg="white", bg="black").place(x=20, y=20)
    entry_dpi2 = tk.Entry(ventana3, width=30)
    entry_dpi2.place(x=20, y=50)

    text_resultado = tk.Text(ventana3, width=70, height=10, bg="black", fg="white")
    text_resultado.place(x=20, y=100)

    def ejecutar_busqueda():
        dpi_buscar = entry_dpi2.get().strip().upper()
        if not dpi_buscar:
            messagebox.showwarning("Falta DPI", "Escribe un DPI para buscar.")
            return
        try:
            con = get_conn()
            cur = con.cursor()
            cur.execute("""
                SELECT id, nombre, estado, edad, dpi
                FROM pacientes
                WHERE dpi = %s
            """, (dpi_buscar,))
            fila = cur.fetchone()
            con.close()

            text_resultado.delete("1.0", tk.END)
            if fila:
                texto = (
                    f"ID: {fila[0]}\n"
                    f"Nombre: {fila[1]}\n"
                    f"Estado: {fila[2]}\n"
                    f"Edad: {fila[3]}\n"
                    f"DPI: {fila[4]}\n"
                )
                text_resultado.insert(tk.END, texto)
            else:
                text_resultado.insert(tk.END, "No se encontró ningún paciente con ese DPI.")
        except Exception as e:
            messagebox.showerror("Error de BD", str(e))

    tk.Button(ventana3, text="BUSCAR", command=ejecutar_busqueda).place(x=280, y=47, height=26)
    entry_dpi2.bind("<Return>", lambda _: ejecutar_busqueda())
    entry_dpi2.focus_set()

#============================= BORRAR PACIENTE ==============================================
def borrar_paciente():
    ventana4 = tk.Toplevel(ventana1)
    ventana4.geometry("900x400")
    ventana4.title("Borrar Pacientes")
    ventana4.config(bg="black")
    

    instrucciones_borrado = tk.Label(ventana4, text="INTRODUZCA EL DPI DEL PACIENTE A BORRAR", fg="white", bg="black")
    instrucciones_borrado.place(x=20, y= 20)

    borrar_entry = tk.Entry(ventana4)
    borrar_entry.place(x=20, y=50, width= 280)
    resultado_text = tk.Text(ventana4, width=35, height=8, bg="black", fg="white")
    resultado_text.place(x=20, y=100)

    def borrar():
        buscar_dpi = borrar_entry.get().strip().upper()
        if not borrar_entry:
            messagebox.showwarning("FALTA INGRESAR DPI", "ingrese DPI")
            return
        try:
            con = get_conn()
            cur = con.cursor()
            cur.execute("SELECT id, nombre FROM pacientes WHERE dpi = %s", (buscar_dpi,))
            fila = cur.fetchone()

            if not fila:
                messagebox.showinfo("ERROR", "no se ha encontrado usuario con ese DPI intente de nuevo")
                con.close()
                return
            resultado_text.delete("1.0", tk.END)
            resultado_text.insert(tk.END, f"Paciente encontrado:\nID: {fila[0]} | Nombre: {fila[1]}\n")

            confirmacion = messagebox.askyesno(
                "Confirmar borrado",
                f"¿Seguro que quieres eliminar al paciente '{fila[1]}' con DPI {buscar_dpi}?"
            )
            if not confirmacion:
                con.close()
                return
            cur.execute("DELETE FROM pacientes WHERE dpi = %s", (buscar_dpi,))
            con.commit()
            con.close()

            messagebox.showinfo("USUSARIO BORRADO", "EXITO PACIENTE CON " f"DPI {buscar_dpi} ELIMINADO")

            resultado_text.insert(tk.END, "CLIENTE ELIMINADO")

        except Exception as e:
            messagebox.ERROR("error de base de datos ", e)

    btn_borrar_cliente = tk.Button(ventana4, text="BORRAR", command=borrar)
    btn_borrar_cliente.place(x=20, y=250, width=280, height=30)
    


# ========= UI: Mostrar todos (nueva ventana) =========
def mostrar_pacientes():
    ventana2 = tk.Toplevel(ventana1)
    ventana2.geometry("900x400")
    ventana2.title("Listado de pacientes")
    ventana2.config(bg="black")

    text_area = tk.Text(ventana2, width=90, height=10, bg="black", fg="white")
    text_area.place(x=70, y=40)

    try:
        con = get_conn()
        cur = con.cursor()
        cur.execute("SELECT id, nombre, estado, edad, dpi FROM pacientes ORDER BY id DESC;")
        pacientes = cur.fetchall()
        con.close()

        text_area.delete("1.0", tk.END)
        for p in pacientes:
            text_area.insert(
                tk.END,
                f"ID: {p[0]} | Nombre: {p[1]} | Estado: {p[2]} | Edad: {p[3]} | DPI/NIT: {p[4]}\n"
            )
    except Exception as e:
        messagebox.showerror("Error de BD", str(e))

# ========= Insertar paciente =========
def agregar_pacientes():
    nombre = entry_nombre.get().strip().upper()
    edad_txt = entry_edad.get().strip().upper()
    dpi = entry_dpi.get().strip().upper()
    estado = var_estado.get().strip().upper()

    if not nombre:
        messagebox.showerror("Error", "El nombre es obligatorio.")
        return
    if not estado:
        messagebox.showerror("Error", "Selecciona un estado del paciente.")
        return
    if not edad_txt.isdigit():
        messagebox.showerror("Error", "La edad debe ser un número entero.")
        return
    if not dpi:
        messagebox.showerror("Error", "El DPI/CUI es obligatorio.")
        return

    edad = int(edad_txt)
    try:
        con = get_conn()
        cur = con.cursor()
        cur.execute(
            "INSERT INTO pacientes (nombre, estado, edad, dpi) VALUES (%s, %s, %s, %s)",
            (nombre, estado, edad, dpi)
        )
        con.commit()
        con.close()

        messagebox.showinfo("Éxito", "Paciente guardado correctamente.")
        entry_nombre.delete(0, tk.END)
        entry_edad.delete(0, tk.END)
        entry_dpi.delete(0, tk.END)
        var_estado.set("")
    except errors.UniqueViolation:
        # Para capturar UNIQUE (dpi repetido) se necesita autocommit o rollback
        try:
            con.rollback()
            con.close()
        except:
            pass
        messagebox.showerror("Error de BD", "El DPI ya existe (UNIQUE).")
    except Exception as e:
        try:
            con.rollback()
            con.close()
        except:
            pass
        messagebox.showerror("Error inesperado", str(e))

# =========== MANDAR EMAIL ============        
def mandar_email():
    ventana5 = tk.Toplevel(ventana1)
    ventana5.config(bg="black")
    ventana5.geometry("900x600")
    ventana5.title("ENVIAR CORREO")
    lbl_correo = tk.Label(ventana5, text="CORREO PACIENTE", fg="white", bg="black")
    lbl_titulo = tk.Label(ventana5, text="ASUNTO CORREO", fg="white", bg="black")
    lbl_cuerpo = tk.Label(ventana5, text="CUERPO CORREO", fg="white", bg="black")
    entry_correo = tk.Entry(ventana5)
    entry_titulo = tk.Entry(ventana5)
    entry_cuerpo = tk.Text(ventana5)
    entry_correo.place(x=150, y=20, width=300)
    entry_titulo.place(x=150, y= 75, width=300)
    entry_cuerpo.place(x=20, y=175, width=600, height=300)
    lbl_correo.place(x=20, y=20)
    lbl_titulo.place(x=20, y=75)
    lbl_cuerpo.place(x=20, y=150)
    

    def email():
        cuerpo = entry_cuerpo.get("1.0", tk.END).strip()
        subjet = entry_titulo.get().strip()
        correo_destino = entry_correo.get().strip()
        if not cuerpo:
            messagebox.showerror("ERROR", "EL CUERPO DEL CORREO NO PUEDE ESTAR VACIO")
            return
        if "@" not in correo_destino:
            messagebox.showerror("ERROR", "CORREO INVALIDO")
            return
        if not subjet:
            messagebox.showerror("ERROR", "NECESITAS PONERLE UN TITULO")
            return

        mensaje = MIMEText(cuerpo)
        mensaje['from'] = correo_persona
        mensaje['To'] = correo_destino
        mensaje['Subject'] = subjet

        try:
            with smtplib.SMTP(smtpserver, puerto) as server:
                server.starttls()
                server.login(correo_persona, contraseña_personal)
                server.sendmail(correo_persona, correo_destino, mensaje.as_string())
                messagebox.showinfo("CORREO", "Correo enviado con éxito.")
        except Exception as e:
            messagebox.showerror("Error", " Error al enviar el correo:", e)

    btn_enviar = tk.Button(ventana5, text="Enviar correo", command=email, height=5, width=84)
    btn_enviar.place(x=20, y=500)

# ========= App =========
init_db()

ventana1 = tk.Tk()
ventana1.title("Registro de Pacientes (PostgreSQL)")
ventana1.geometry("1000x320")
ventana1.config(bg="black")

lbl_nombre = tk.Label(ventana1, text="NOMBRE PACIENTE", fg="white", bg="black")
lbl_edad   = tk.Label(ventana1, text="EDAD PACIENTE",  fg="white", bg="black")
lbl_dpi    = tk.Label(ventana1, text="DPI/CUI",        fg="white", bg="black")
lbl_estado = tk.Label(ventana1, text="ESTADO PACIENTE",fg="white", bg="black")

entry_nombre = tk.Entry(ventana1)
entry_edad   = tk.Entry(ventana1)
entry_dpi    = tk.Entry(ventana1)

var_estado = tk.StringVar(value="")
opciones_estado = [
    "ESTADO CRITICO",
    "URGENCIA GRAVE",
    "URGENCIA MODERADA",
    "URGENCIA LEVE",
    "CONSULTA EXTERNA"
]
menu_estado = tk.OptionMenu(ventana1, var_estado, *opciones_estado)

btn_guardar = tk.Button(ventana1, text="CONFIRMAR", command=agregar_pacientes)
btn_buscar  = tk.Button(ventana1, text="BUSCAR PACIENTE", command=buscar_cliente)
btn_mostrar = tk.Button(ventana1, text="MOSTRAR PACIENTES", command=mostrar_pacientes)
btn_borrar = tk.Button(ventana1, text="BORRAR PACIENTES", command=borrar_paciente)
btn_mandar_email = tk.Button(ventana1, text="MANDAR CORREO", command=mandar_email)

# Layout
lbl_nombre.place(x=40,  y=40)
entry_nombre.place(x=220, y=40, width=300)

lbl_edad.place(x=40,   y=90)
entry_edad.place(x=220, y=90, width=120)

lbl_dpi.place(x=40,   y=140)
entry_dpi.place(x=220, y=140, width=200)

lbl_estado.place(x=40,   y=190)
menu_estado.place(x=220, y=190, width=220)

btn_guardar.place(x=220, y=240, width=140, height=32)
btn_mostrar.place(x=400, y=240, width=180, height=32)
btn_buscar.place(x=600, y=240, width=180, height=32)
btn_borrar.place(x=800, y=240, width=180, height=32)
btn_mandar_email.place(x=1000, y= 240, width=180, height=32)

ventana1.mainloop()
