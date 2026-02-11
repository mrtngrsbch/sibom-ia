# Guía de Actualización de Datos del Chatbot

Para mantener el chatbot actualizado con los últimos boletines oficiales, sigue estos pasos:

## 1. Descargar nuevos boletines (Scraper)
Usa el scraper de Python para descargar los últimos archivos JSON.
```bash
cd python-cli
# Ejemplo: Descargar los últimos 10 boletines de Merlo (ID 22)
python3 sibom_scraper.py --url https://sibom.slyt.gba.gob.ar/cities/22 --limit 10 --skip-existing
```

## 2. Actualizar el Índice (RAG)
Este es el paso más importante para que el chatbot "vea" los nuevos archivos de forma instantánea y eficiente.
```bash
cd python-cli
python3 indexar_boletines.py
```
Este script leerá todos los archivos JSON en la carpeta `boletines/` y actualizará el archivo `boletines_index.json` que utiliza el chatbot.

## 3. Reiniciar el Chatbot (Opcional)
El chatbot tiene un cache de 10 minutos para el índice. Si quieres ver los cambios inmediatamente, puedes reiniciar el servidor de Next.js o simplemente esperar 10 minutos.

---

### ¿Por qué es necesario indexar?
El chatbot ahora maneja casi 2000 documentos. Sin el índice, el bot tendría que leer todos los archivos en cada pregunta, lo que causaría que se cuelgue (como sucedía antes). El índice permite que el bot sea ultra-rápido.
