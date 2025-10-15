import tkinter as tk
from tkinter import messagebox
import psycopg2
from psycopg2 import sql, errors
import smtplib
from email.mime.text import MIMEText
from tkcalendar import Calendar #### Se debe de instalar tkcalendar "pip install tkcalendar"
from datetime import datetime, date
from tkinter import ttk ########

#   DB_settings
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
                correo  TEXT NOT NULL,
                edad    INTEGER,
                dpi     TEXT UNIQUE
            );
        """)
        # Citas (se agregó campo codigo_cita)
        cur.execute("""
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
        """)
        con.commit()
        con.close()
    except Exception as e:
        messagebox.showerror("Error de BD", f"No se pudo inicializar la BD:\n{e}")

#   FUNCION AGREGAR PACIENTES Y AGREGARLA EN LA BASE DE DATOS 
def agregar_pacientes():
    ventana_agregar_pacientes = tk.Toplevel(ventana_principal)
    ventana_agregar_pacientes.geometry("900x600")
    ventana_agregar_pacientes.config(bg= "#0b1220")
    ventana_agregar_pacientes.title("AGREGAR PACIENTES")
    lbl_nombre = tk.Label(ventana_agregar_pacientes, text="NOMBRE DEL PACIENTE  :", bg="#0b1220", fg="#CAF0F8")
    lbl_edad = tk.Label(ventana_agregar_pacientes, text="EDAD DEL PACIENTE  :", bg="#0b1220", fg="#CAF0F8")
    lbl_dpi = tk.Label(ventana_agregar_pacientes, text="DPI/CUI DEL PACIENTE  :", bg="#0b1220", fg="#CAF0F8")
    lbl_correo = tk.Label(ventana_agregar_pacientes, text="CORREO DEL PACIENTE  :", bg="#0b1220", fg="#CAF0F8")
    entry_nombre = tk.Entry(ventana_agregar_pacientes)
    entry_edad = tk.Entry(ventana_agregar_pacientes)
    entry_dpi = tk.Entry(ventana_agregar_pacientes)
    entry_correo = tk.Entry(ventana_agregar_pacientes)
    lbl_nombre.place(x=20, y=50)
    lbl_edad.place(x=20, y=150)
    lbl_dpi.place(x=20, y=250)
    lbl_correo.place(x=20,y =350)
    entry_nombre.place(x=200, y=50, height=30, width=600)
    entry_edad.place(x=200, y=150, height=30, width=600)
    entry_dpi.place(x=200, y=250, height=30, width=600)
    entry_correo.place(x=200, y=350, height=30, width=600)
    

    def agregar():
        nombre = entry_nombre.get().strip().upper()
        edad = entry_edad.get().strip()
        dpi = entry_dpi.get().strip().upper()
        correo = entry_correo.get().strip()
        if not nombre or not edad or not dpi or not correo:
            messagebox.showwarning("Campos vacíos", "Por favor, complete todos los campos.")
            return
        if not "@" in correo or not "." in correo:
            messagebox.showwarning("Correo inválido", "Por favor, ingrese un correo válido.")
            return
        try:
            edad_int = int(edad)
            if edad_int < 0 or edad_int > 120:
                messagebox.showwarning("Edad inválida", "Por favor, ingrese una edad válida.")
                return
        except ValueError:
            messagebox.showwarning("Edad inválida", "Por favor, ingrese una edad numérica.")
            return
        try:
            con = get_conn()
            cur = con.cursor()
            cur.execute(
                "INSERT INTO pacientes (nombre, correo, edad, dpi) VALUES (%s, %s, %s, %s)",
                (nombre, correo, edad_int, dpi)
            )
            con.commit()
            con.close()

            coonfirmacion = messagebox.askyesno("CONFIRMACION", "¿DESEA AGREGAR AL SIGUIENTE PACIENTE?\n\nNOMBRE: " + nombre + "\nEDAD: " + edad + "\nDPI/CUI: " + dpi + "\nCORREO: " + correo)
            if coonfirmacion:
                messagebox.showinfo("ÉXITO", "PACIENTE AGREGADO EXITOSAMENTE")
            else:
                return
            entry_nombre.delete(0, tk.END)
            entry_edad.delete(0, tk.END)
            entry_dpi.delete(0, tk.END)
            entry_correo.delete(0, tk.END)
        except errors.UniqueViolation:
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
    btn_guardar = tk.Button(ventana_agregar_pacientes, text="GUARDAR PACIENTE", fg="#023E8A", bg="#CAF0F8", command=agregar)
    btn_guardar.place(x=350, y=450, height=40, width=200)

def borrar_paciente():
    ventana_borrar = tk.Toplevel(ventana_principal)
    ventana_borrar.geometry("325x400")
    ventana_borrar.title("Borrar Pacientes")
    ventana_borrar.config(bg= "#0b1220")
    

    instrucciones_borrado = tk.Label(ventana_borrar, text="INTRODUZCA EL DPI DEL PACIENTE A BORRAR", bg="#0b1220", fg="#CAF0F8")
    instrucciones_borrado.place(x=20, y= 20)

    borrar_entry = tk.Entry(ventana_borrar)
    borrar_entry.place(x=20, y=50, width= 280)
    resultado_text = tk.Text(ventana_borrar, width=35, height=8, bg="#0b1220", fg="#CAF0F8")
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

    btn_borrar_cliente = tk.Button(ventana_borrar, text="BORRAR",fg="#023E8A",bg="#CAF0F8", command=borrar)
    btn_borrar_cliente.place(x=20, y=250, width=280, height=30)

def mandar_email():
    ventana_email = tk.Toplevel(ventana_principal)
    ventana_email.config(bg="#0b1220")
    ventana_email.geometry("650x600")
    ventana_email.title("ENVIAR CORREO")
    lbl_correo = tk.Label(ventana_email, text="CORREO PACIENTE", bg="#0b1220", fg="#CAF0F8")
    lbl_titulo = tk.Label(ventana_email, text="ASUNTO CORREO", bg="#0b1220", fg="#CAF0F8")
    lbl_cuerpo = tk.Label(ventana_email, text="CUERPO CORREO", bg="#0b1220", fg="#CAF0F8")
    entry_correo = tk.Entry(ventana_email)
    entry_titulo = tk.Entry(ventana_email)
    entry_cuerpo = tk.Text(ventana_email,bg="#0b1220", fg="#CAF0F8")
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

    btn_enviar = tk.Button(ventana_email, text="Enviar correo", command=email, height=5, width=84, fg="#023E8A", bg="#CAF0F8")
    btn_enviar.place(x=20, y=500)

def cita():
    ventana_cita = tk.Toplevel()
    ventana_cita.geometry("500x500")
    ventana_cita.title("AGENDA DE CITAS")
    ventana_cita.config(bg="#0b1220")

    # --- Calendario ---
    cal = Calendar(
        ventana_cita,
        selectmode="day",
        mindate=date.today(),
        background="#023E8A",
        foreground="white",
        headersbackground="#0077B6",
        normalbackground="#90E0EF",
        weekendbackground="#48CAE4"
    )
    cal.pack(pady=10)

    # --- Entradas ---
    lbl_dpi_paciente = tk.Label(ventana_cita, text="DPI DEL PACIENTE:", bg="#0b1220", fg="#CAF0F8")
    lbl_hora = tk.Label(ventana_cita, text="Hora (HH:MM):", bg="#0b1220", fg="#CAF0F8")
    entry_dpi_paciente = tk.Entry(ventana_cita)
    entry_hora = tk.Entry(ventana_cita)

    lbl_dpi_paciente.place(x=20, y=300)
    entry_dpi_paciente.place(x=200, y=300, width=200)
    lbl_hora.place(x=20, y=350)
    entry_hora.place(x=200, y=350, width=200)

    # --- Botón guardar ---
    def guardar_cita():
        fecha_seleccionada = cal.get_date()
        hora = entry_hora.get().strip()
        dpi_paciente = entry_dpi_paciente.get().strip().upper()

        # Validaciones
        if not hora:
            messagebox.showwarning("Hora faltante", "Por favor, ingrese una hora (HH:MM).")
            return
        if not dpi_paciente:
            messagebox.showwarning("DPI faltante", "Por favor, ingrese el DPI del paciente.")
            return
        try:
            datetime.strptime(hora, "%H:%M")
        except ValueError:
            messagebox.showwarning("Formato inválido", "Ingrese la hora en formato HH:MM (24 horas).")
            return

        fecha_sql = datetime.strptime(fecha_seleccionada, "%m/%d/%y").strftime("%Y-%m-%d")

        # Verificar paciente
        try:
            con = get_conn()
            cur = con.cursor()
            cur.execute("SELECT id, nombre FROM pacientes WHERE dpi = %s", (dpi_paciente,))
            paciente = cur.fetchone()

            if not paciente:
                messagebox.showerror("Paciente no encontrado", "No existe ningún paciente con ese DPI.")
                con.close()
                return

            paciente_id, nombre_paciente = paciente

            # Generar código único de cita (3 letras nombre + día)
            iniciales = nombre_paciente.strip().upper()[:3]
            dia = datetime.strptime(fecha_seleccionada, "%m/%d/%y").day
            codigo_cita = f"{iniciales}{dia:02d}"

            # Confirmación
            confirmar = messagebox.askyesno(
                "CONFIRMAR CITA",
                f"¿Desea agendar la cita?\n\n"
                f"Paciente: {nombre_paciente}\n"
                f"Fecha: {fecha_sql}\n"
                f"Hora: {hora}\n"
                f"Código: {codigo_cita}"
            )
            if not confirmar:
                con.close()
                return

            # Guardar cita
            cur.execute(
                "INSERT INTO citas_medicas (paciente_id, fecha, hora, motivo, codigo_cita) VALUES (%s, %s, %s, %s, %s)",
                (paciente_id, fecha_sql, hora, "Cita general", codigo_cita)
            )
            con.commit()
            con.close()

            messagebox.showinfo("Éxito", f"Cita agendada correctamente.\nCódigo: {codigo_cita}")
            entry_dpi_paciente.delete(0, tk.END)
            entry_hora.delete(0, tk.END)

        except Exception as e:
            messagebox.showerror("Error de BD", f"Ocurrió un error:\n{e}")
            try:
                con.rollback()
                con.close()
            except:
                pass

    btn_guardar = tk.Button(
        ventana_cita, text="GUARDAR CITA", command=guardar_cita,
        bg="#CAF0F8", fg="#023E8A", height=2, width=20
    )
    btn_guardar.place(x=150, y=420)


init_db()        

"""Se comenta ya que no se usa, queda como referencia"""
#ventana_principal = tk.Tk()
#ventana_principal.title("MENU DE OPCIONES")
#ventana_principal.geometry("300x900")
#ventana_principal.config(bg="#0b1220")
#btn_agregar_pacientes = tk.Button(text="AGREGAR PACIENTE", fg="#023E8A",bg="#CAF0F8", command=agregar_pacientes)
#btn_elimminar_pacientes = tk.Button(text="BORRAR PACIENTES", fg="#023E8A", bg="#CAF0F8", command=borrar_paciente)
#btn_mandar_email = tk.Button(text="ENVIAR CORREO", fg="#023E8A", bg="#CAF0F8", command=mandar_email)
#btn_agendar_cita = tk.Button(text="AGENDAR CITA", fg="#023E8A", bg="#CAF0F8", command=cita)
#btn_agregar_pacientes.place(x=20,y=50, height=50, width=260)
#btn_elimminar_pacientes.place(x=20, y=150, height=50, width=260)
#btn_mandar_email.place(x=20, y=250, height=50, width=260)
#btn_agendar_cita.place(x=20, y=350, height=50, width=260)#
###### NUEVO MENÚ PRINCIPAL ######

def menu_principal():
    try:
        ventana_principal.destroy()
    except:
        pass

    ventana_principal = tk.Tk()
    ventana_principal.title("MENÚ PRINCIPAL")
    ventana_principal.geometry("400x600")
    ventana_principal.config(bg="#0b1220")

    lbl_titulo = tk.Label(
        ventana_principal,
        text="MENÚ PRINCIPAL",
        font=("Arial", 18, "bold"),
        bg="#0b1220",
        fg="#CAF0F8"
    )
    lbl_titulo.pack(pady=20)

    # Botones principales del menú
    btn_pacientes = tk.Button(
        ventana_principal,
        text="PACIENTES",
        fg="#023E8A",
        bg="#CAF0F8",
        width=25,
        height=2,
        command=ventana_pacientes 
    )

    btn_calendario = tk.Button(
        ventana_principal,
        text="CALENDARIO",
        fg="#023E8A",
        bg="#CAF0F8",
        width=25,
        height=2,
        command=cita
    )

    btn_agendar = tk.Button(
        ventana_principal,
        text="AGENDAR CITA",
        fg="#023E8A",
        bg="#CAF0F8",
        width=25,
        height=2,
        command=cita
    )

    btn_correo = tk.Button(
        ventana_principal,
        text="ENVIAR CORREO",
        fg="#023E8A",
        bg="#CAF0F8",
        width=25,
        height=2,
        command=mandar_email
    )

    # Ubicación de botones
    btn_pacientes.pack(pady=10)
    btn_calendario.pack(pady=10)
    btn_agendar.pack(pady=10)
    btn_correo.pack(pady=10)

    ventana_principal.mainloop()



def ventana_pacientes():
    # Crear ventana
    ventana = tk.Toplevel()
    ventana.title("PACIENTES")
    ventana.geometry("700x500")
    ventana.config(bg="#0b1220")
    
    tk.Label(ventana, text="LISTA DE PACIENTES", font=("Arial", 14, "bold"), bg="#0b1220", fg="#CAF0F8").pack(pady=10)

    columns = ("id", "nombre", "correo", "edad", "dpi")
    tree = ttk.Treeview(ventana, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col.upper())
        tree.column(col, width=120)
    tree.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

    # Función para cargar pacientes desde la base de datos
    def cargar_pacientes():
        try:
            con = get_conn()
            cur = con.cursor()
            cur.execute("SELECT id, nombre, correo, edad, dpi FROM pacientes")
            pacientes = cur.fetchall()
            con.close()

            for row in tree.get_children():
                tree.delete(row)
            for p in pacientes:
                tree.insert("", tk.END, values=p)
        except Exception as e:
            messagebox.showerror("Error DB", f"No se pudo cargar pacientes:\n{e}")

    cargar_pacientes()
#doble lcick
    def abrir_detalle(event):
        selected_item = tree.selection()
        if not selected_item:
            return
        paciente = tree.item(selected_item)["values"]
        abrir_detalle_paciente(paciente)

    tree.bind("<Double-1>", abrir_detalle)
#boton '+'
    def abrir_agregar():
        agregar_pacientes()
        cargar_pacientes() 

    btn_mas = tk.Button(ventana, text="+", font=("Arial", 22, "bold"), fg="#023E8A", bg="#CAF0F8", command=abrir_agregar)
    btn_mas.place(relx=0.9, rely=0.9, anchor="center", width=60, height=60)


######## edita los datos del paciente

def abrir_detalle_paciente(paciente):
    paciente_id, nombre, correo, edad, dpi = paciente
    ventana = tk.Toplevel()
    ventana.title(f"Detalle paciente: {nombre}")
    ventana.geometry("500x500")
    ventana.config(bg="#0b1220")

    # Campos editables
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

    # Botón para guardar cambios
    def guardar_cambios():
        nuevo_nombre = entry_nombre.get().strip()
        nuevo_correo = entry_correo.get().strip()
        nuevo_dpi = entry_dpi.get().strip().upper()
        if not nuevo_nombre or not nuevo_correo or not nuevo_dpi:
            messagebox.showwarning("Campos vacíos", "Todos los campos son obligatorios")
            return
        try:
            con = get_conn()
            cur = con.cursor()
            cur.execute(
                "UPDATE pacientes SET nombre=%s, correo=%s, dpi=%s WHERE id=%s",
                (nuevo_nombre, nuevo_correo, nuevo_dpi, paciente_id)
            )
            con.commit()
            con.close()
            messagebox.showinfo("Éxito", "Paciente actualizado correctamente")
            ventana.destroy()
        except Exception as e:
            messagebox.showerror("Error DB", f"No se pudo actualizar:\n{e}")

    tk.Button(ventana, text="GUARDAR CAMBIOS", fg="#023E8A", bg="#CAF0F8", command=guardar_cambios).place(x=150, y=220, width=200, height=40)


menu_principal() 

