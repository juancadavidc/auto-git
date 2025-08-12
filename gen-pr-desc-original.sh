#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------
# gen-pr-desc-validated.sh
# 1) Genera PR_DESCRIPTION_.md a partir del diff con origin/main usando llama3.1 (Ollama)
# 2) Valida/corrige el Markdown con otro LLM (VALIDATOR_MODEL) para asegurar formato/estilo
# ---------------------------------------

# -------- Configurables por ENV / argumentos --------
MODEL="${MODEL:-llama3.1}"                     # Primer LLM para redactar la descripción del PR
VALIDATOR_MODEL="${VALIDATOR_MODEL:-qwen2.5:7b}"  # LLM para validar/corregir Markdown
OUTFILE="${1:-PR_DESCRIPTION.md}"              # Archivo de salida principal
VALIDATED_OUT="${OUTFILE%.md}.validated.md"    # Archivo corregido por el validador
REPORT_OUT="${OUTFILE%.md}.validation.txt"     # Reporte del validador

MAX_DIFF_LINES="${MAX_DIFF_LINES:-4000}"       # Cortar diff muy grande
NUM_CTX="${NUM_CTX:-8192}"                     # Contexto para el redactor
VALIDATOR_NUM_CTX="${VALIDATOR_NUM_CTX:-8192}" # Contexto para el validador

export LC_ALL=C

# -------- Comprobaciones de entorno --------
command -v git >/dev/null 2>&1 || { echo "ERROR: git no está instalado/en PATH."; exit 1; }
command -v ollama >/dev/null 2>&1 || { echo "ERROR: ollama no está instalado/en PATH."; exit 1; }
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "ERROR: aquí no hay repo git."; exit 1; }

# -------- Contexto del repo y diff --------
echo "› Actualizando refs remotas…"
git fetch origin --quiet

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
REPO_NAME="$(basename -s .git "$(git config --get remote.origin.url || echo 'repo')")"
GIT_USER="$(git config user.name || echo 'unknown')"
GIT_EMAIL="$(git config user.email || echo 'unknown@example.com')"

DIFF="$(git diff origin/main || true)"
if [[ -z "${DIFF}" ]]; then
  echo "No hay diferencias contra origin/main. Nada que describir."
  exit 0
fi

DIFF_LINES=$(printf "%s\n" "$DIFF" | wc -l | awk '{print $1}')
TRUNCATED="false"
if (( DIFF_LINES > MAX_DIFF_LINES )); then
  DIFF="$(printf "%s\n" "$DIFF" | head -n "${MAX_DIFF_LINES}")"
  TRUNCATED="true"
fi

CHANGED_FILES="$(git diff --name-status origin/main | sed 's/^/\- /')"

# -------- Prompt redactor (1ª pasada) --------
PROMPT_FILE="$(mktemp -t pr_prompt.XXXXXX)"

cat > "$PROMPT_FILE" <<'HEADER'
Eres un revisor senior de código. A partir del DIFF que te doy, redacta una descripción de Pull Request en **Markdown** siguiendo estrictamente la plantilla.
Reglas IMPORTANTES:
- Escribe en español claro y profesional.
- Sé específico sobre qué cambió y por qué, mencionando módulos/archivos relevantes.
- Resume riesgos, impactos y consideraciones de despliegue si aplica.
- Donde se piden “Links”, deja el texto entre paréntesis tal cual si no hay enlace real (no inventes URLs).
- NO agregues secciones extra. NO cambies los títulos. Rellena la plantilla exactamente como está.
- Si el diff fue truncado, indícalo en “Attachments” con una nota breve: “El diff fue truncado para el modelo”.

Ahora, rellena la siguiente PLANTILLA **tal cual**:

# Title

**Please include a descriptive title and summary of the change, understandable by most developers (even if they haven't worked in the project previously) in this section.**
**AVOID empty descriptions or only pasting the JIRA ticket. Those descriptions will be rejected as they are non-compliant with this guide.**

The _bare-minimum_ description should have the following parts:

### Type of change

You should describe here what type of change are you trying to merge. Is it a bugfix? A new feature? Adding more tests?
A reviewer should know this by reading your description alone, without needing to open the JIRA ticket and grasp the context about it. You need to select one or more of the next labels in this PR:

**This PR contains a:**

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Non-functional feature (if the PR contains changes in: swagger, readme, config)
--- CONTEXTO DEL REPO ---
HEADER

cat >> "$PROMPT_FILE" <<EOF
Repositorio: ${REPO_NAME}
Rama actual: ${CURRENT_BRANCH}
Autor local: ${GIT_USER} <${GIT_EMAIL}>

Archivos cambiados (name-status):
${CHANGED_FILES}

¿Diff truncado?: ${TRUNCATED}

--- DIFF (contra origin/main) ---
EOF

printf "%s\n" "$DIFF" >> "$PROMPT_FILE"

# -------- Redacción (1ª pasada) --------
echo "› Generando descripción con ${MODEL} (Ollama)…"

# Construimos el comando en un array para evitar expandir arrays vacíos con set -u
cmd=(ollama run)
if ollama --help 2>/dev/null | grep -q -- '--num_ctx'; then
  cmd+=(--num_ctx "$NUM_CTX")
fi
cmd+=("$MODEL")

RESPONSE="$("${cmd[@]}" < "$PROMPT_FILE")"
printf "%s\n" "$RESPONSE" > "$OUTFILE"
echo "✅ PR generado: $OUTFILE"

# -------- Prompt validador (2ª pasada) --------
VALIDATOR_PROMPT="$(mktemp -t pr_validator.XXXXXX)"
cat > "$VALIDATOR_PROMPT" <<'VHDR'
Eres un revisor de calidad de documentación técnica.
Tarea:
1) Analiza el siguiente Markdown de descripción de PR.
2) Verifica cumplimiento estricto de la plantilla (títulos, secciones, orden).
3) Verifica estilo Markdown: encabezados con #, listas con -, checklists con - [ ], negritas **…**, enlaces en formato [Texto](Link).
4) No inventes enlaces ni datos. Mantén (Link) si no existe URL real.
5) Corrige solo formato/estilo/estructura. No alteres el significado.
6) Devuelve SIEMPRE dos bloques:
   a) **REPORTE** en texto breve con hallazgos (cada punto en una línea).
   b) **MARKDOWN_FINAL**: el Markdown completo y corregido.

Responde únicamente con:
---REPORTE---
<reporte breve, línea por hallazgo o “OK: sin observaciones”>
---MARKDOWN_FINAL---
<markdown completo corregido>
VHDR

VALIDATOR_INPUT="$(mktemp -t pr_input_md.XXXXXX)"
{
  echo "### DOCUMENTO A VALIDAR (Markdown):"
  echo
  cat "$OUTFILE"
} > "$VALIDATOR_INPUT"

echo "› Validando/corriendo Markdown con ${VALIDATOR_MODEL} (Ollama)…"

val_cmd=(ollama run)
if ollama --help 2>/dev/null | grep -q -- '--num_ctx'; then
  val_cmd+=(--num_ctx "$VALIDATOR_NUM_CTX")
fi
val_cmd+=("$VALIDATOR_MODEL")

VALIDATION_RAW="$(cat "$VALIDATOR_PROMPT" "$VALIDATOR_INPUT" | "${val_cmd[@]}")"

REPORT="$(printf "%s" "$VALIDATION_RAW" | awk '/---REPORTE---/{flag=1;next}/---MARKDOWN_FINAL---/{flag=0}flag')"
MARKDOWN_FINAL="$(printf "%s" "$VALIDATION_RAW" | awk '/---MARKDOWN_FINAL---/{flag=1;next}flag')"

if [[ -z "${MARKDOWN_FINAL// }" ]]; then
  echo "⚠️  El validador no devolvió separadores esperados; guardando salida cruda."
  printf "%s\n" "$VALIDATION_RAW" > "$REPORT_OUT"
  cp "$OUTFILE" "$VALIDATED_OUT"
else
  printf "%s\n" "$REPORT" > "$REPORT_OUT"
  printf "%s\n" "$MARKDOWN_FINAL" > "$VALIDATED_OUT"
fi

echo "✅ Validación completada."
echo "   - Markdown validado: $VALIDATED_OUT"
echo "   - Reporte:           $REPORT_OUT"

# Limpieza
rm -f "$PROMPT_FILE" "$VALIDATOR_PROMPT" "$VALIDATOR_INPUT"