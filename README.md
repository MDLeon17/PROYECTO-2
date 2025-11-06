# sistema de gestion de pacientes, clinica de Licda. Beatriz Velasquez

Sistema de escritorio para la administración de pacientes y agendamiento de citas en una clinica de rehabilitacion. 

## Descripción General

Este es un sistema destinado al uso en windows con la funcion de manejar a pacientes en un consultorio, se conecta a una base de datos PostgreSQL remota para asegurar la persistencia de los datos.

Se desarrolla utilizando python y tkinter para la construcción de la interfaz gráfica de usuario (GUI).

## Características Principales

## gestion de pacientes
  Funcionalidad completa para Crear, Leer, Actualizar y Eliminar registros de pacientes. Incluye un visualizador de lista y la capacidad de editar la información de cada paciente.
##Agendar citas
   Un módulo de calendario que permite seleccionar una fecha y muestra únicamente los horarios disponibles para ese día, evitando conflictos de agendamiento.
   

  * **Visualización de Calendario:** Una vista de calendario que permite consultar las citas programadas para cualquier día seleccionado.
  * **Envío de Correos:** Integración con un servidor SMTP (Gmail) para enviar correos electrónicos a los pacientes, como recordatorios de citas.
  * **Base de Datos:** El sistema se conecta a una base de datos PostgreSQL. Las tablas `pacientes` y `citas_medicas` se crean automáticamente si no existen al iniciar la aplicación.

## Requisitos de Instalación FERNANDO MODIFICA ESTO

Para ejecutar este proyecto, es necesario contar con Python  instalado y algunas librerias extras

1.  **Clonar o descargar** el repositorio del proyecto.

2.  **Instalar las dependencias** necesarias a través de `pip`. Abrir una terminal en el directorio del proyecto y ejecutar:

    ```bash
    pip install tkcalendar
    pip install psycopg2-binary
    pip install Pillow
    ```

  Nota: Tkinter es para la interfaz y smtplib para los correos, estos forman parte de la biblioteca estándar de Python.

# configuracion del email
# Debe modificar los campos que se encuentran despues de "#email settings" con los datos personales del correo para enviar desde la direccion de email deseada
correo_persona = "su_correo_remitente@gmail.com"
contraseña_personal = "Contraseña de su correo"
smtpserver = "smtp.gmail.com"
puerto = 587