# Auto PR Desc

🤖 Generador automático de descripciones de Pull Request usando IA local con Ollama.

## 📋 Descripción

Auto PR Desc es una herramienta que utiliza modelos de IA locales (vía Ollama) para generar automáticamente descripciones estructuradas y profesionales de Pull Requests en español. La herramienta analiza los cambios en tu rama actual comparándolos con `origin/main` y genera una descripción completa siguiendo una plantilla estándar.

### ✨ Características principales

- 🚀 **Generación automática**: Analiza diffs de Git y genera descripciones profesionales
- 🔍 **Validación opcional**: Segundo modelo de IA para revisar y mejorar la calidad
- 📁 **Prompts externos**: Archivos de configuración separados para fácil mantenimiento
- 🎯 **Plantilla estándar**: Sigue formato consistente para PRs empresariales
- ⚙️ **Configurable**: Variables de entorno y opciones de línea de comandos
- 🌐 **Local**: Utiliza Ollama para mantener todo en tu máquina

## 🛠️ Prerequisitos

### Software requerido

- **Git**: Para análisis de cambios y repositorio
- **Ollama**: Para ejecutar modelos de IA localmente
- **Bash**: Shell compatible (Linux/macOS/WSL)

### Modelos de Ollama

Instala los modelos requeridos:

```bash
# Modelo principal (recomendado)
ollama pull llama3.1

# Modelo de validación (opcional)
ollama pull qwen2.5:7b
```

## 📦 Instalación

1. **Clona el repositorio:**
   ```bash
   git clone https://github.com/tu-usuario/auto-pr-desc.git
   cd auto-pr-desc
   ```

2. **Hacer ejecutable el script:**
   ```bash
   chmod +x gen-pr-desc.sh
   ```

3. **Opcional - Agregar al PATH:**
   ```bash
   # Agregar a tu ~/.bashrc o ~/.zshrc
   export PATH="$PATH:/ruta/a/auto-pr-desc"
   ```

## 🚀 Uso

### Uso básico

```bash
# Generar descripción básica
./gen-pr-desc.sh

# Especificar archivo de salida
./gen-pr-desc.sh mi-pr-descripcion.md

# Generar con validación
./gen-pr-desc.sh --validate
```

### Opciones disponibles

```bash
./gen-pr-desc.sh [ARCHIVO_SALIDA] [--validate] [--help]
```

- `ARCHIVO_SALIDA`: Nombre del archivo de salida (por defecto: `PR_DESCRIPTION.md`)
- `--validate`: Habilita el paso de validación con segundo modelo
- `--help, -h`: Muestra ayuda completa

### Variables de entorno

```bash
# Modelo principal
export MODEL="llama3.1"

# Modelo de validación  
export VALIDATOR_MODEL="qwen2.5:7b"

# Límite de líneas del diff
export MAX_DIFF_LINES=4000

# Tamaño de ventana de contexto
export NUM_CTX=8192
```

## 📋 Ejemplo de flujo de trabajo

1. **Hacer cambios en tu rama:**
   ```bash
   git checkout -b feature/nueva-funcionalidad
   # ... hacer cambios ...
   git add .
   git commit -m "Implementar nueva funcionalidad"
   ```

2. **Generar descripción del PR:**
   ```bash
   ./gen-pr-desc.sh --validate
   ```

3. **Revisar y usar la descripción:**
   ```bash
   cat PR_DESCRIPTION.md
   # Copiar contenido para usar en GitHub/GitLab
   ```

## 📁 Estructura del proyecto

```
auto-pr-desc/
├── gen-pr-desc.sh              # Script principal mejorado
├── gen-pr-desc-original.sh     # Respaldo de versión original
├── prompts/
│   ├── pr-generation.txt       # Prompt para generación principal
│   └── pr-validation.txt       # Prompt para validación
└── README.md                   # Documentación del proyecto
```

## ⚙️ Configuración avanzada

### Personalizar prompts

Los archivos en `prompts/` se pueden modificar para adaptar el estilo y formato de las descripciones generadas:

- **`pr-generation.txt`**: Controla cómo se genera la descripción inicial
- **`pr-validation.txt`**: Define cómo se valida y mejora la descripción

### Modelos alternativos

Puedes usar diferentes modelos de Ollama según tus necesidades:

```bash
# Modelos más ligeros
export MODEL="llama3.1:8b"
export VALIDATOR_MODEL="llama3.1:8b"

# Modelos más potentes (requieren más RAM)
export MODEL="llama3.1:70b" 
export VALIDATOR_MODEL="llama3.1:70b"
```

## 🐛 Solución de problemas

### Error: "git is not installed"
```bash
# Ubuntu/Debian
sudo apt-get install git

# macOS
brew install git
```

### Error: "ollama is not installed"
```bash
# Instalar Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Verificar instalación
ollama --version
```

### Error: "not inside a git repository"
```bash
# Inicializar repositorio si es necesario
git init
git remote add origin <tu-repositorio>
```

### Diff muy grande
Si el diff es muy extenso, ajusta el límite:
```bash
export MAX_DIFF_LINES=8000
./gen-pr-desc.sh
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🙏 Agradecimientos

- [Ollama](https://ollama.ai/) por proporcionar una forma fácil de ejecutar modelos de IA localmente
- Comunidad de desarrolladores que contribuye a mejorar las herramientas de desarrollo

## 📞 Soporte

Si encuentras algún problema o tienes sugerencias:

1. Revisa los [Issues existentes](../../issues)
2. Crea un [Nuevo Issue](../../issues/new) con detalles del problema
3. Incluye información de tu sistema y versiones de software

---

**¿Te gusta el proyecto? ⭐ Dale una estrella en GitHub!**
