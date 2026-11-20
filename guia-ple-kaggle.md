# Guía de participación — Google · Agent Harness on Physical-Engineering's Last Exam (PLE)

> Guía sintetizada a partir de las páginas oficiales de la competencia en Kaggle (Description, Submission Requirements, Tracks and Awards, Acknowledgements/Evaluation), del sitio oficial **ple-bench.com**, del repositorio **github.com/google-research/ple** y del paper **arXiv:2610.30537v2** ("PLE: Physical-Engineering's Last Exam").
> Fecha de compilación: 17 de noviembre de 2026. Verifica los números en las fuentes oficiales antes de enviar: los organizadores pueden actualizar detalles.

---

## 1. Ficha rápida

| Campo | Valor |
|---|---|
| Competencia | Google - Agent Harness on Physical-Engineering's Last Exam (Kaggle Featured Hackathon) |
| Anfitrión / patrocinador | Google LLC — Google Cloud AI Research |
| Socios | Mercor (creación y validación de tareas, entorno Archipelago) + Stanford, NYU, U. Washington, UNC Chapel Hill, Harvard, Columbia |
| Premio total | **$400,000 USD** — 1º $250k · 2º $100k · 3º $50k |
| Formato | Hackathon destacado; **no otorga puntos ni medallas de Kaggle** |
| Inicio | 9 de noviembre de 2026 |
| Envío final | **5 de enero de 2027, 23:59 UTC** |
| Fin Etapa 1 | 19 de enero de 2027 (Top 100 avanzan a Etapa 2) |
| Resultados finales | 26 de enero de 2027 |
| Elegibilidad | 18+, máximo 5 personas por equipo, una entrada por equipo, excluidas regiones sancionadas |
| Entrada | 1 commit de GitHub (harness + `submission.yaml` + `artifacts/`) + 1 Writeup Kaggle ≤ 2,000 palabras |
| Modelos | 8 modelos fundacionales patrocinados por Google (las claves las inyecta el evaluador) |
| Benchmark | PLE: 85 tareas de ingeniería real (29 dev públicas + 56 test ocultas) en 4 disciplinas |
| Condición de premio | Score medio en Etapa 2 **≥ 0.138** y estar en la **frontera de Pareto rendimiento-costo** |
| Licencia de entrega | Código: Apache-2.0 o MIT · Writeup del ganador: CC BY 4.0 |

---

## 2. Descripción general de la competencia

### 2.1 Problema central y objetivo

Construir un **harness** (andamiaje de agente autónomo) de código abierto, emparejarlo con uno de los 8 modelos fundacionales patrocinados por Google y resolver **Physical-Engineering's Last Exam (PLE)**: 85 tareas de ingeniería de largo horizonte, revisadas por expertos licenciados, en cuatro disciplinas — **estructural (10), civil (18), eléctrica (27) y mecánica (30)**.

Resolver una tarea **no es responder una pregunta**: es completar un **entregable de ingeniería facturable y verificable** — un paquete de cálculos, un modelo 3D sin colisiones en formato IFC4, un tablero eléctrico dimensionado, un memorando firmable por un revisor licenciado — a partir de una carpeta de proyecto realista.

Tu entrega tiene dos mitades:
1. **Código**: el harness que ejecuta las 56 tareas ocultas en la Etapa 2.
2. **Análisis**: un Writeup de Kaggle con hallazgos investigativos (el 40% de la rúbrica premia insight y razonamiento de ingeniería, no solo score).

### 2.2 Contexto científico y económico

- Los modelos frontera superan el 90% en benchmarks de "trivia" académica, pero **el mejor agente en PLE alcanza 50.6%** (Claude Opus 5.5 en Claude Code), gastando **27M de tokens y 63 minutos por tarea** en promedio. La ingeniería física es un deporte distinto: ruteo de tuberías de agua helada a través de 7 planos alrededor de una retícula estructural desplazada y 104 aspersores, sin atravesar una viga de acero con un ducto.
- **Motivación económica** (del paper): la brecha de infraestructura de EE. UU. para 2024–2033 es de **$3.7 billones** (ASCE); la inversión mundial necesaria hacia 2040 se estima en **$94 billones**; los servicios de ingeniería en EE. UU. reportan **>$300 mil millones/año**. Si la IA funciona aquí, comprimiría ciclos de diseño de meses a días.
- **Motivación científica**: los benchmarks existentes (EngiBench, EngDesign, Frontier-Eng, ElecBench, DrafterBench) son trivia de libro de texto, diseño "de juguete" o sub-tareas aisladas — están saturados y ninguno exige navegar un corpus multi-formato y emitir un entregable facturable. PLE sigue la serie de "last exams": Humanity's Last Exam (conocimiento) → Agents' Last Exam (trabajo digital) → PLE (trabajo que construye el mundo físico).

### 2.3 Anatomía del benchmark

Cada tarea tiene 4 partes: **instrucción** (el encargo que recibiría un ingeniero en un proyecto activo), **entorno** (sistema de archivos del proyecto), **especificación de entregables** (archivos de producción exigidos) y **grader** (rúbrica ponderada o verificador ejecutable con referencias retenidas). Los entornos se empaquetan en formato APEX y exponen sus aplicaciones vía **MCP** (sistema de archivos, documentos, hojas de cálculo, PDF, correo, calendario, chat) más un sandbox de ejecución de código.

| Disciplina | Tareas | Dev | Test oculto | Entregables típicos |
|---|---:|---:|---:|---|
| Estructural | 10 | 4 | 6 | Verificaciones de cargas (gravedad, viento, sismo), dimensionamiento de elementos y conexiones, revisiones de planos por comentarios |
| Civil | 18 | 9 | 9 | Asentamiento y capacidad portante, estrategia de cimentación, trazado de sitio, nivelación y drenaje, secuencias constructivas, estimaciones de costo |
| Eléctrica | 27 | 9 | 18 | Cálculos de carga y capacidad, respuestas de revisión de planos, energización, dimensionamiento de cables, especificaciones |
| Mecánica | 30 | 7 | 23 | Enfriamiento y control, ruteo MEP sin colisiones, equivalencia de equipos, vida útil de tanques, validación de resistencia al fuego |
| **Total** | **85** | **29** | **56** | 249 entregables en total |

**Los dos tipos de tarea (complementarios):**

| | Expert-authored (44) | Co-authored (41) |
|---|---|---|
| Origen | Escritas de punta a punta por ingenieros licenciados (red de expertos de Mercor) | Semilla de ingeniero → construidas por pipeline agéntico Creator–Solver → validadas/intensificadas por expertos |
| Entornos | 12 entornos compartidos | 41 entornos individuales |
| Corpus | 62.8 archivos/tarea en promedio; centrado en documentos (51.6% PDF, 25.2% hojas de cálculo, 22.4% texto/correo); 3.0 MB/tarea | 58.7 archivos/tarea; añade CAD/BIM (12.9%), esquemas (7.1%), portales web, código; 38.1 MB/tarea (12.6×) |
| Grading | Rúbrica ponderada de verificadores binarios (941 ítems, 21.4/tarea, pesos 1–10) | Restricciones duras/soft (~29.9/tarea) + score objetivo económico |
| Entregables | 1.1 archivos/tarea (77.6% memo .docx) | 4.9 archivos/tarea (62.5% hojas de cálculo/datos, 21% narrativas, 13% CAD/BIM) |

**Fórmula de score de las co-authored** (las más difíciles):

```
s = 0.4·p + 0.6·G·O'
```
- `p` = fracción de todas las restricciones pasadas
- `G` ∈ {0,1} = **puerta dura** de seguridad y factibilidad (todas las restricciones hard deben pasar)
- `O'` = score objetivo normalizado contra el diseño "naive" pero cumplidor (para tareas de "diseño más barato": O = c_bound/c, costo vs. cota inferior certificada)

### 2.4 Cómo se crearon las tareas (pipeline co-authored)

1. **Semilla de experto**: un ingeniero licenciado define situación, restricciones físicas/de código, objetivo y formato del entregable (interfaz de nominación).
2. **Task Creator** (Claude Opus 5 en Claude Code): investigación profunda para construir prompt, entorno multi-formato y grader ejecutable con entregable de referencia. Reglas: realidad (fuentes licenciables), dificultad auténtica (sin trampas ocultas), tareas de ingeniería no de "respuestas buscables", entregables verificables.
3. **Task Solver** (Hermes, N=3 corridas paralelas, sin acceso al grader ni referencias): **puerta de dificultad** — solo avanza si la media de los 3 intentos queda bajo el umbral; si no, el Creator intensifica (modifica el objetivo, añade restricciones, o vuelve a deep-research si el entorno es pobre).
4. **Validación Mercor**: ingeniero independiente valida realismo y coherencia, e intensifica la dificultad añadiendo ítems propios.

Los expertos fueron remunerados a tarifas profesionales (~$4,663/tarea expert-authored; ~$3,157/tarea co-authored). El 52% del benchmark se mantiene **privado** (56 tareas) para evitar saturación y contaminación de datos de entrenamiento.

### 2.5 Línea base: resultados del paper (85 tareas, media de 3 corridas)

| Configuración (modelo en harness) | Score | Costo/tarea |
|---|---:|---:|
| Claude Opus 5.5 en Claude Code | **50.6%** | $17.18 |
| GPT 6 Astra en Codex | 48.3% | $9.15 |
| Claude Sonnet 5.5 en Antigravity | 45.2% | — |
| Gemini 4 Argon (mejor harness) | 43.2% | $8.21 |
| Claude Opus 5 | 42.6% | — |
| Claude Fable 5 en Claude Code | 34.9% | — |
| Grok 4.7 en Grok Build | 32.0% | — |
| Gemini 3.8 Flash en Claude Code | 28.2% | $2.55 |
| GLM 5.2 (mejor harness) | 25.3% | — |
| Qwen3 Coder 480B, MiniMax M2, Kimi K2, Llama 4 Maverick | < 7% | < $0.20 |

Datos clave: 14 modelos × 7 harnesses públicos (Antigravity, Claude Code, Codex, Hermes, **OpenCode**, OpenHands, Pi; GPT 6 Astra solo en Codex; Grok solo en su harness). En Claude Code, Opus 5.5 puntúa < 50% en 48 de 85 tareas; mecánica (40.5%) y estructural (46.6%) son las más difíciles; civil la más fácil (69.9%); co-authored más duras que expert-authored (48.0% vs 53.1%). Dos tareas puntúan 0% en todas las corridas; siete superan 90%.

---

## 3. Requisitos técnicos

### 3.1 Anatomía de la entrada

Una entrada es **un único commit** de un repositorio git, con esta estructura en la raíz:

```
submission.yaml      nombre, model_api, comandos install/serve, env
serve.py             servidor WebSocket (cualquier lenguaje; las muestras usan Python)
harness.py           bucle del agente, o envoltorio de un agente existente
artifacts/           salidas del dev set generadas por eval/run.py (nunca a mano)
...                  lo demás que necesites: requirements.txt, prompts, agente vendido
```

Reglas transversales:
- **Licencia**: Apache-2.0 o MIT obligatoria en la raíz.
- Repo completo (incluida la historia git) ≤ **1 GiB**: cada versión histórica de `artifacts/` pesa en la historia; mantén artifacts compactos o haz squash.
- Si el repo es privado durante la competencia, instala la app GitHub **ple-submission** y hazlo público al cierre.
- Nunca registres ni retengas contenido de tareas (incluidas las ocultas).

### 3.2 `submission.yaml`

```yaml
name: mi-harness                          # 2-39 chars: a-z, 0-9, -, empieza con letra/dígito
model_api: google-cloud/claude-opus-5-5   # uno de los 8 modelos patrocinados
install: >-                               # opcional; UNA vez en build, root, con internet
  uv venv --python 3.12 /opt/harness/venv
  && uv pip install --python /opt/harness/venv/bin/python -r {src}/requirements.txt
serve: /opt/harness/venv/bin/python {src}/serve.py   # requerido; arranca en $PORT
env:                                      # opcional; valores SIEMPRE entre comillas
  LOG_LEVEL: "info"
  REASONING_EFFORT: "high"
```

| Campo | Reglas |
|---|---|
| `name` | 2–39 caracteres (`a-z`, `0-9`, `-`), empieza con letra o dígito |
| `model_api` | `google-cloud/<id>` (los 8 de la tabla 3.8) |
| `install` | comando shell; `{src}` se expande a `/opt/harness/src` |
| `serve` | comando shell; `{src}` y `{port}` se expanden; comillas balanceadas |
| `env` | pares `NAME: "value"` entre comillas (`true`, `1.10`, `0755` sin comillas los parsea YAML como bool/número). Nunca secretos. Prohibido sobreescribir: `PORT`, `HOME`, `USER`, `HTTP_PROXY`/`HTTPS_PROXY`/`ALL_PROXY`/`NO_PROXY`/`NODE_USE_ENV_PROXY` y las variables del modelo |

Restricciones del archivo: ≤ **16 KiB**; claves de nivel superior desconocidas → rechazo; `{src}` y `{port}` son los únicos placeholders expandidos.

### 3.3 Ciclo de vida: build y serve

**Contenedor de build (`install`) — se ejecuta una vez:**
- `debian:bookworm`, como root, con internet, **timeout 30 min**.
- Preinstalado: `uv` (`/opt/harness/bin/uv`), Node 22 (`/opt/harness/node`; `npm -g`), `git`, `curl`, toolchain de build, `python3`.
- Solo se conserva `/opt/harness` (≤ **2 GiB comprimido / 8 GiB descomprimido**); los symlinks deben resolver dentro de `/opt/harness`; lo instalado fuera (p. ej. `apt-get`) se descarta.
- El contenedor serve usa la **misma imagen base** → los binarios compilados en build corren idénticos en evaluación. Fija versiones de dependencias.

**Contenedor serve (`serve`) — uno nuevo por tarea:**
- `/opt/harness` montado **read-only**; corre en `/opt/harness/src` como uid 1000.
- Recursos: **2 CPUs, 4 GB RAM**, `/tmp` y `$HOME` tmpfs de **1 GB** cada uno, límite de 512 procesos.
- Debe aceptar la conexión WebSocket en `0.0.0.0:$PORT` **dentro de 120 s** (si no, la tarea falla y penaliza).
- Salida solo vía `HTTPS_PROXY` (solo el endpoint del modelo es alcanzable; DNS directo deshabilitado; descargas de paquetes en runtime bloqueadas). `stdout/stderr` se capturan como log del serve.

### 3.4 Protocolo WebSocket

Una conexión por tarea, frames de texto UTF-8 JSON (≤ **16 MiB** por frame, un objeto por frame). El evaluador abre con:

```json
{"type": "task", "protocol": 1, "session": "...", "instruction": "<enunciado verbatim>",
 "workdir": "/app",
 "limits": {"agent_timeout_sec": 21600, "exec_timeout_sec": 600, "max_output_bytes": 100000,
            "max_write_bytes": 10000000},
 "mcp_servers": [{"name": "apps", "url": "http://127.0.0.1:8000/mcp/", "transport": "streamable-http"}]}
```

**Peticiones (hasta 8 concurrentes; el resto se encola) → resultados:**

| Petición | Devuelve |
|---|---|
| `{"type":"exec","id":"1","command":"ls -la","timeout_sec":120}` | `exit_code`, `output` (stdout+stderr; head+tail preservados >100 KB), `truncated`, `timed_out` |
| `{"type":"read_file","id":"2","path":"/app/data.csv"}` | `ok`, `content_b64`, `size`, `truncated` (tope 10 MB) |
| `{"type":"write_file","id":"3","path":"/app/out/report.md","content_b64":"...","append":false}` | `ok`, `size`; crea directorios padre; ≤10 MB por llamada |
| `{"type":"http","id":"4","method":"POST","url":"<mcp_servers>","headers":{},"body_b64":"..."}` | `ok`, `status`, `headers`, `body_b64`, `truncated` (cuerpos ≤10 MB) |

Detalles críticos:
- `exec` corre `bash -c` en el contenedor de tarea desde `workdir` como usuario de tarea; **solo el estado del sistema de archivos persiste** entre llamadas (`cd` y variables de shell no). Timeout efectivo = `min(timeout_sec, exec_timeout_sec, tiempo restante)`; por defecto 120 s; timeout → `timed_out: true`, `exit_code: 124`.
- Para archivos >10 MB: encadenar `write_file` con `append: true`.
- `http` solo alcanza los `mcp_servers` declarados de la tarea (algunos `tools/list` devuelven cientos de herramientas, >500 KB).
- Operación fallida → `ok: false` + `error`. Frames malformados devuelven error sin abortar, pero **>20 frames malformados terminan la sesión**.

**Mensajes unidireccionales (sin respuesta):**
- `{"type":"log","text":"..."}` — añade una línea al log del trial.
- `{"type":"usage","model":"...","input_tokens":N,"output_tokens":N,"cache_read_tokens":N}` — reporta el uso de tokens por llamada.
- `{"type":"done","final_message":"..."}` — **cierra la tarea limpiamente**. El resumen lo lee el juez de rúbrica.
- `{"type":"error","message":"..."}` — aborta temprano; los archivos ya escritos **sí se califican**.

**Al expirar el tiempo**: el evaluador envía `{"type":"cancel","reason":"timeout"}` y cierra el socket 10 s después. Al recibir `cancel`: detén llamadas al modelo en vuelo y envía `done` con tu mejor resumen — **tanto `final_message` como los archivos en disco cuentan**. Si el socket se cierra antes de `done`/`error` (o nunca escuchaste), la tarea falla y penaliza.

### 3.5 Variables de entorno del modelo (inyectadas por el evaluador)

| Variable | Valor |
|---|---|
| `PORT` | Puerto de tu servidor WebSocket |
| `MODEL_API` / `MODEL_NAME` | Tu string `model_api` y el identificador a mandar en las peticiones |
| `MODEL_BASE_URL` / `MODEL_API_KEY` | Endpoint **OpenAI-compatible** (suele terminar en `/v1`) y clave, para TODOS los modelos |
| `OPENAI_BASE_URL` / `OPENAI_API_KEY` | Idénticas a las anteriores (el SDK estándar de OpenAI funciona sin configuración) |
| `ANTHROPIC_BASE_URL` / `ANTHROPIC_API_KEY` | Endpoint nativo Anthropic (sin `/v1`), solo para Claude |
| `GOOGLE_GEMINI_BASE_URL` / `GEMINI_API_KEY` | Endpoint nativo Gemini (sin `/v1`), solo para Gemini |
| Tu `env` | Se pasa tal cual |

### 3.6 `artifacts/` (reglas)

- Generada automáticamente por `eval/run.py`: una subcarpeta por tarea dev con `files/<ruta en contenedor>`, `final_message.md` y un `manifest.json` superior que registra la corrida y hace **hash de todos los archivos del harness**.
- Sin comprimir, ≤ **512 MiB** y ≤ **10,000 archivos**; sin Git LFS ni symlinks; sin archivos >95 MiB.
- Si el harness cambia después de generar artifacts, `kit artifacts` lo detecta → re-corre el dev set y commitea todo junto (`git add -A`). Cambios solo de README/LICENSE/CHANGELOG dan una nota en vez de warning.
- Tarea dev con carpeta faltante, symlink, archivo >95 MiB o sin entregables calificables → **0**.

### 3.7 Kit local (PLE Competition Kit) — etapas de `kit check`

Requisitos: `uv` + **Docker local** (contenedores `linux/amd64`; en Apple Silicon emula; `DOCKER_HOST` remoto rechazado). Para correr el dev set: `uv tool install harbor==0.20.0 --with websockets` + `HF_TOKEN` (dataset de tareas gated en Hugging Face).

| Etapa | Qué verifica |
|---|---|
| `submission.yaml` | Todo el esquema y reglas de campos |
| `files` | Archivos referenciados por `serve` commiteados; escaneo de claves API filtradas; avisa cambios sin commit |
| `build` | Ejecuta `install` en el builder y empaqueta `/opt/harness` |
| `model` | Prompt de prueba desde el contenedor serve vía proxy de salida (conectividad del modelo) |
| `listen` | `serve` binda y acepta WebSocket en `$PORT` en ≤120 s |
| `smoke` | Tarea humo end-to-end: escribir `/app/hello.txt` y mandar `done` |
| `cancel` | (con `--cancel-test`) cancela a los 45 s y verifica que el harness mande `done` limpio |
| `artifacts` | Valida `artifacts/` contra las reglas del evaluador y que esté commiteada |

Comandos esenciales:

```bash
uv run python -m kit check ../mi-harness [--cancel-test] [--rebuild]
uv run python eval/run.py ../mi-harness              # corre el dev set y escribe artifacts/
uv run python eval/run.py ../mi-harness --tasks <id> # re-corre UNA tarea
uv run python -m kit artifacts ../mi-harness         # valida artifacts como el evaluador
uv run python eval/run.py --artifacts ../mi-harness  # re-califica artifacts commiteados (solo llama al juez)
uv run python eval/run.py --regrade runs/<name>-<time>  # re-califica sin repetir las corridas
```

Logs detallados en `~/.cache/plebench/<name>/`: `build.log`, `serve.log`, `egress.log` (conexiones permitidas/bloqueadas), `relay.log` (protocolo), `check.json`. Otros subcomandos: `kit validate`, `build`, `up`, `models`.

Para probar un modelo `google-cloud/` localmente: proxy local de Vertex AI con tu propio proyecto de Google Cloud (`kit/model_proxy/start.sh`; variables `VERTEXAI_PROJECT`, `MODEL_PROXY_URL`, `MODEL_PROXY_KEY`) — **facturado a tu cuenta**; ver alternativas gratuitas en §8.3.

### 3.8 Los 8 modelos patrocinados

Las entradas corren **solo** en modelos patrocinados por Google (el evaluador inyecta la clave por submission; tus claves y servidores no son aceptados). El proxy bloquea claves custom (`.env`), servidores de modelo externos y búsqueda web. La lista puede actualizarse con modelos nuevos:

| `model_api` | Modelo | Familia |
|---|---|---|
| `google-cloud/gemini-4-argon` | Gemini 4 Argon | Gemini |
| `google-cloud/gemini-3.8-flash` | Gemini 3.8 Flash | Gemini |
| `google-cloud/gemini-3.1-pro-preview` | Gemini 3.1 Pro (preview) | Gemini |
| `google-cloud/gemma-4-26b` | Gemma 4 26B A4B | Gemma (open-weight) |
| `google-cloud/claude-opus-5-5` | Claude Opus 5.5 | Claude |
| `google-cloud/gpt-oss-120b` | gpt-oss 120B | Open-weight |
| `google-cloud/glm-5.2` | GLM 5.2 | GLM (open-weight) |
| `google-cloud/llama-4-maverick` | Llama 4 Maverick 17B 128E | Llama (open-weight) |

**Tips por familia (de la documentación oficial):**
- Todos soportan tool calling. Por defecto corren a su nivel máximo de razonamiento (`max` en Claude y GLM; `high` en Gemini, gpt-oss, Kimi, MiniMax) tanto en el evaluador como en `kit/model_proxy`; pasa `reasoning_effort` explícito para bajar el nivel.
- **Claude Opus 5.5**: rechaza `temperature`, `top_p`, `top_k` y bloques `thinking` con `budget_tokens` → omítelos. `max_tokens` generoso (32,000 es buen default). El caching solo se activa donde marcas: `"cache_control": {"type": "ephemeral"}` en el system prompt y en el mensaje más reciente (Claude permite 4 marcas); sin marcas cada turno paga el input completo de la conversación — muchas veces el costo.
- **Gemini 4 Argon**: acepta `reasoning_effort` (`low`/`medium`/`high`); devuelve HTTP 400 si le mandas `thinkingBudget`. Mantén `max_tokens` ≤ 65,536. Cachea por su cuenta.
- **General**: stream de respuestas largas o timeouts generosos (los turnos de razonamiento largo pueden quedar silenciosos varios minutos). Reintenta 429/timeouts/5xx con backoff exponencial; **nunca reintentes 400**. Controla `limits.agent_timeout_sec` y envuelve las llamadas antes del deadline.

---

## 4. Arquitectura del harness: decisiones y sus motivaciones

Esta sección explica el **porqué** de cada decisión de diseño — tanto de la infraestructura que impone la competencia (que no puedes cambiar) como las que tú debes tomar en tu harness (que definen tu score y costo).

### 4.1 A. Motivos de la infraestructura de la competencia

**1. Contenedor de tarea sin red + proxy de salida solo al modelo.**
*Regla*: la tarea no tiene internet; tu serve solo alcanza el endpoint del modelo declarado.
*Motivos*: (a) obliga a razonar con el corpus local — como un ingeniero real que trabaja horas sin consultar la web, que es exactamente la habilidad que se quiere medir; (b) bloquea fuga de contenido de tareas ocultas a servicios externos (protege el 56% privado del benchmark de contaminación); (c) iguala las condiciones: nadie gana por acceso a datos que otros no tienen; (d) cierra la puerta a delegar el trabajo a un modelo distinto del declarado.

**2. Tres contenedores separados (serve / evaluador / tarea) con un protocolo JSON mínimo.**
*Motivos*: (a) todas las acciones del harness pasan por el evaluador → el solver **nunca** accede al task container ni a los graders/rúbricas/referencias (diseño heredado del paper: "the solver can never reach the grader or the reference deliverables"); (b) hace la plataforma agnóstica del lenguaje del harness (cualquier WebSocket sirve), permitiendo envolver agentes existentes; (c) aísla fallos: un crash del harness no compromete el entorno de tarea ni el grader.

**3. Build una vez con internet; runtime sin descargas.**
*Motivos*: (a) reproducibilidad — lo que se evalúa es exactamente el bundle construido, con binarios idénticos (la misma imagen base en build y serve); (b) seguridad de supply chain: sin paquetes improvisados en runtime; (c) límites explícitos (2 GiB comprimido, repo ≤1 GiB) evitan entradas-monstruo y hacen el costo de evaluación predecible.

**4. `artifacts/` con manifest hash + re-ejecución de muestra aleatoria del dev set.**
*Motivos*: (a) verifican que el código commiteado es el que produjo los artefactos (hash de manifest ↔ estado del harness); (b) detectan salidas pregrabadas o hard-codeadas → descalificación; (c) los organizadores re-califican tus `artifacts/` con el **juez oficial** (Claude Opus 5.5), de modo que tu juez local no influye en el ranking — así el desarrollo gratuito con jueces open-weight es válido.

**5. Límite de 6 h por tarea + mensaje `cancel` con ventana de 10 s.**
*Motivos*: (a) los entregables reales de ingeniería son trabajo de horas (el paper promedia 63 min/tarea el mejor agente; las co-authored, 97 min) — un límite de minutos trivializaría el benchmark; (b) el `cancel` con `done` final es un incentivo de arquitectura deliberado: los archivos escritos y el `final_message` cuentan aunque expire el tiempo → premia harnesses que escriben el entregable temprano y refinan después, y penaliza los que "planean hasta morir".

**6. Límites finos por acción (exec 600 s, output 100 KB head+tail, escritura 10 MB, frame 16 MiB, 8 concurrentes, 512 procesos, 2 CPU, 4 GB RAM).**
*Motivos*: (a) un comando colgante no puede bloquear la tarea (timeout por request); (b) head+tail de la salida conserva lo útil para depurar sin desbordar el contexto del agente; (c) los tope de escritura en base64 existen porque los formatos de ingeniería (DXF/DWG/IFC) son binarios y pesados; (d) recursos modestos impiden la fuerza bruta masiva (p. ej., cientos de ejecuciones paralelas de simuladores) y reflejan estaciones de ingeniería reales; (e) >20 frames malformados cortan la sesión: disciplina de protocolo obligatoria.

**7. Score híbrido `s = 0.4·p + 0.6·G·O'` con puerta dura `G` (tareas co-authored).**
*Motivos*: una rúbrica binaria no distingue un diseño "meramente cumplidor" de uno económicamente competitivo (dos esquemas de cables pueden pasar todas las verificaciones y uno costar 20% más instalar); pero un objetivo de costo puro se puede "hackear" entregando algo inseguro o infactible → la puerta `G` obliga a pasar **todas** las restricciones hard antes de cobrar el crédito del objetivo. Evidencia del paper: el mejor agente cumple **91%** de las restricciones individuales en promedio, pero solo **41.3%** de sus ítems pasan **todas** las duras — "producir un diseño totalmente seguro y factible mientras empuja su costo hacia la cota sigue siendo la dificultad central de PLE".

**8. El Writeup con análisis de fallos vale 40 de 100 puntos (Etapa 1).**
*Motivos*: la competencia es también un experimento científico; los organizadores publican scores y costos de todos los sistemas. Los fallos documentados con ablations ("añadimos X y el score dev pasó de A a B") enseñan a la comunidad qué arquitecturas funcionan — por eso te piden mostrar fallos reales (callouts mal leídos, cláusula equivocada, errores de unidades, parar temprano) e ideas que fracasaron.

**9. Modelos patrocinados con claves inyectadas + frames `usage` obligatorios.**
*Motivos*: (a) la frontera Pareto exige costos comparables y verificables — el proxy ve los tokens reales; (b) elimina ventajas por precio de API propia o abonos corporativos; (c) el bloqueo de claves custom (`.env`) y servidores externos en Etapa 2 garantiza que todos juegan con los mismos endpoints.

**10. Top 100 + pre-screening + 3 corridas independientes (168 runs).**
*Motivos*: (a) la Etapa 1 filtra calidad de análisis y ejecutabilidad sin quemar el test set oculto; el pre-screening en un subconjunto pequeño de tareas ocultas desalienta entradas que "se construyen solo para el dev set"; (b) las 3 corridas responden a la varianza medida: el rango medio de una celda tarea-harness en 3 corridas es **15.4 pts**, y 105 de 595 celdas varían ≥30 pts — una sola corrida es estadísticamente ruido; la media de set es estable (σ 0.3–1.8 pts).

**11. Umbral de premio 0.138 y ranking por Pareto.**
*Motivos*: (a) el umbral (≈ la puntuación de Gemini 3.1 Pro en el paper, 14.2%) evita premiar sistemas triviales que quedan "en la frontera" por ser baratos y pésimos; (b) el Pareto codifica la tesis económica de la competencia: lo relevante no es el máximo score a cualquier costo, sino el mejor trabajo por dólar — por eso Gemini 3.8 Flash (28.2% por $2.55) es una apuesta seria y Codex ($35.15) no.

### 4.2 B. Motivos de las decisiones de tu harness (guiadas por la evidencia)

**1. Elegir el modelo primero; el harness, después.**
*Evidencia*: el modelo importa mucho más que el harness — dispersión de hasta **50 puntos entre modelos** vs. mediana de **3.0 puntos** entre harnesses para el mismo modelo (rango 0.7–12.1).
*Decisión*: barre ≥2 modelos (idealmente familias distintas) sobre el dev set con tu harness v1 antes de invertir en ingeniería de harness; commitea tu mejor `model_api` para la Etapa 2. Esto además es literalmente el criterio de rúbrica #3 (15 pts).

**2. Caching de prefijos en Claude (y saber qué familia cachea sola).**
*Evidencia*: sin marcas `cache_control` cada turno repaga el input completo de la conversación — "muchas veces el costo"; con 4 marcas (system + mensajes recientes) el costo por tarea cae drásticamente. Gemini cachea por su cuenta.
*Decisión*: implementa el marcado de caché desde el día 1 en las llamadas Anthropic; es la palanca de costo más grande del harness y define tu posición en el Pareto.

**3. Razonamiento al máximo por defecto; explícito cuando el costo apriete.**
*Evidencia*: los modelos patrocinados corren a `max`/`high` por defecto en el evaluador; el Pareto muestra configuraciones baratas competitivas (Gemini 3.8 Flash retiene el 56% del score top por el 15% del costo).
*Decisión*: expón `reasoning_effort` como variable de `env` para poder abaratar iteraciones y ajustar el punto Pareto final sin reescribir código.

**4. Streaming + backoff exponencial en 429/5xx; nunca reintentar 400.**
*Evidencia*: los turnos de razonamiento largo quedan silenciosos minutos (timeouts HTTP prematuros matan llamadas caras); HTTP 400 significa petición malformada — reintentar solo gasta; y en Etapa 2 "invalid requests (HTTP 400) or unrecovered agent crashes and timeouts count against your score".
*Decisión*: streaming en toda llamada larga; reintentos solo de errores transitorios, con backoff y jitter; trata 400 como bug tuyo.

**5. Entregable temprano, pasos pequeños verificados, presupuesto de tiempo por paso.**
*Evidencia*: el **25.3%** de las corridas con 0% terminó sin entregable calificable; los graders inspeccionan rutas, nombres y formatos exactos de los entregables (la "gran mayoría de cada score"); el juez de rúbrica lee además tu `done.final_message`; y el patrón documentado de harnesses de alto score es: "leer la instrucción completa, inspeccionar los archivos iniciales, trabajar en pasos pequeños verificados, escribir un entregable inicial temprano y refinarlo, y presupuestar el tiempo para mandar `done` antes de `agent_timeout_sec`".
*Decisión*: el bucle principal debe (i) reescribir el enunciado en un plan de entregables con rutas exactas, (ii) crear esqueletos de todos los entregables en la primera fase, (iii) verificar cada paso con lecturas/comandos antes de avanzar, (iv) chequear `time_left()` antes de cada fase y abortar a una fase de cierre si queda poco margen.

**6. Citar cláusulas aplicadas (cláusula + valor + documento fuente).**
*Evidencia*: el grader co-authored verifica que los requisitos listados por el solver existen en las referencias — "successful navigation of the corpus becomes a metric in the final grading".
*Decisión*: que tu agente mantenga un registro estructurado de cada requisito aplicado (cláusula, valor, archivo/página) y lo incluya en los entregables y en `final_message`. Convierte la navegación del corpus en puntos, no en costo.

**7. Compaction de contexto y límites por familia.**
*Evidencia*: una tarea co-authored consume **39.3M tokens y 97 min** (vs. 15.6M/31 min en expert-authored); Opus 5.5 rechaza `temperature`/`top_p`/`top_k` y `thinking.budget_tokens`; Gemini exige `max_tokens` ≤ 65,536; los modelos de contexto pequeño necesitan `MAX_OUTPUT_TOKENS` más bajo.
*Decisión*: compaction periódica del historial (la muestra `custom-openai` la implementa), sin tocar el system prompt ni el resumen de entregables pendientes; configuración de sampling por familia leída de `MODEL_API`.

**8. Envolver un agente existente vs. loop propio.**
*Evidencia*: 7 harnesses públicos logran 47.3–50.6% con Opus 5.5 — envolver no te relega; pero el costo sí varía (Claude Code $17.18 vs. Codex $35.15 a scores similares).
*Decisión*: para prototipar rápido, envuelve (hermes-opus, pi-opus, agy-gemini usan `taskbridge.py`/`Relay` para puentear un CLI subprocess → WebSocket); para competir en el Pareto, un loop propio (`minimal` <250 líneas como base) te da control de caching, compaction y presupuesto. `node-protocol` demuestra que ni siquiera necesitas Python.

**9. Promediar 3 corridas; no sobre-ajustar a tareas sueltas.**
*Evidencia*: varianza intra-tarea enorme (rango medio 15.4 pts; 105/595 celdas ≥30 pts) mientras la media del set es estable (σ 0.3–1.8).
*Decisión*: toda mejora debe demostrarse sobre el dev set completo (o un subconjunto aleatorio grande), no sobre la tarea que se comportó mal ayer; el ruido de una tarea no es señal.

**10. MCP vía `Session.http` para las apps de oficina; shell como fallback.**
*Evidencia*: los entornos exponen aplicaciones (filesystem, documentos, hojas de cálculo, PDF, correo, calendario, chat) como servidores MCP Streamable-HTTP; algunas `tools/list` superan 500 KB (cientos de herramientas); Pi, sin soporte MCP, llega a todo por shell.
*Decisión*: consume MCP cuando exista (los emails y hojas son canales oficiales de requisitos); pero no dependas de él — un envoltorio por shell es un plan B válido y el paper confirma que funciona.

**11. Fallos de infraestructura ≠ fallos del agente (manéjalos distinto).**
*Evidencia*: los organizadores reintentan automáticamente fallos del evaluador y rate limits del endpoint patrocinado sin penalización; pero HTTP 400, crashes no recuperados y timeouts del agente penalizan. En el paper, el 4.3% de los ceros fue time budget/error del lado del agente.
*Decisión*: distingue en tu lógica de errores qué es recuperable (429/5xx → backoff) de qué es terminal (400 → log y sigue); y jamás dejes que una excepción no manejada muera sin `done`/`error` — `taskbridge` envía un `final_message` de fallback incluso si `solve` lanza.

### 4.3 Síntesis: los modos de fallo dictan la arquitectura

El paper descompone el **23.2% de corridas con score 0** en: 25.3% sin entregable calificable, 4.3% time budget/error del agente, 70.4% entregable que el grader puntúa 0 (2,020 en co-authored por eq. 1, 817 en rúbricas, 726 en las puertas all-or-nothing de site-design y MEP-coordination, donde un choque duro o una fila sin servir = 0 y un sitio infactible da máx. 50%).

| Modo de fallo | Contramedida de arquitectura |
|---|---|
| Sin entregable / parar temprano | Entregable-primero + presupuesto de tiempo + `done` con resumen |
| Restricciones duras incumplidas (41.3% vs 91% individuales) | Verificación explícita de cada restricción hard antes de "dar por bueno" el diseño (loop plan-verify) |
| Requisitos mal citados / corpus mal navegado | Registro estructurado de cláusulas (§4.2-6) |
| Errores de unidades / callouts mal leídos | Extraer números con código (no a ojo) y verificarlos contra los documentos fuente |
| Golpear puertas all-or-nothing | En tareas de ruteo/trazado: clash-check propio antes de declarar listo; servir TODAS las filas/equipos exigidos |
| Tiempo agotado | Chequeo de `time_left()` por fase + fase de cierre obligatoria |

---

## 5. Evaluación y métricas

### 5.1 Requisitos mínimos (4 checks para que tu entrada entre a Etapa 1)

1. **Writeup Kaggle** (≤2,000 palabras) cubriendo los 5 criterios de rúbrica, con imagen de portada en la Media Gallery y **3 figuras obligatorias**: (1) diagrama de arquitectura, (2) gráfico score-vs-costo, (3) desglose de fallos en las 29 tareas dev. Los borradores sin enviar no se juzgan.
2. **Repositorio GitHub + SHA de 40 caracteres** (`git rev-parse HEAD`) bajo `Project Links`, con el SHA al inicio del Writeup. El commit debe incluir `submission.yaml` (apuntando a uno de los 8 `google-cloud/*`), `serve.py`/`harness.py`, licencia Apache-2.0 o MIT, y `artifacts/` sin comprimir, y pasar `kit check` + `kit artifacts`.
3. `model_api` en los 8 oficiales para la Etapa 2 (no se requiere cuenta de facturación de Google Cloud para el dev local: puedes experimentar y generar `artifacts/` con cualquier modelo open-weight autoalojado o API/suscripción personal). En Etapa 2 el proxy bloquea claves custom y Google provee la clave **sin costo**.
4. Pasar `kit check` y `kit artifacts`. Cambiar `model_api` al objetivo `google-cloud/<id>` después de generar artifacts en un modelo local **no descalifica** si documentas tu setup en el Writeup; los organizadores re-calificarán con el juez oficial. Si usaste un juez open-weight (`JUDGE_MODEL`), decláralo.

Las entradas elegibles pueden pre-filtrarse en un subconjunto pequeño de tareas ocultas.

### 5.2 Etapa 1 — rúbrica del Writeup (100 pts; Top 100 avanzan)

| Criterio | Pts | Qué buscan los jueces | Estrategia |
|---|---:|---|---|
| 1. Insight y análisis de fallos | 25 | Enseñar algo no obvio: fallos reales del dev set, ablations controladas ("añadimos X y pasamos de A a B"), ideas que fallaron | Lleva un lab notebook desde el día 1; documenta cada idea fallida con su ablation |
| 2. Razonamiento de ingeniería | 25 | Recorrer una tarea dev concreta comparando la trayectoria de tu agente contra el flujo de un ingeniero licenciado: dónde sostuvo el razonamiento, dónde tomó atajos, qué habilidades de dominio (leer CAD/PDF, tablas de código, solvers) separaron éxitos de fallos | Elige 1–2 tareas con trayectorias ricas; narra el proceso con capturas |
| 3. Generalización entre modelos | 15 | ≥2 modelos (incluidos open-weight locales o APIs personales), idealmente de familias distintas; tabla comparativa; qué ayuda a todos y qué solo a uno; commitea tu mejor `model_api` | Tu comparación Gemini vs. open-weight (§8.3) cumple esto gratis |
| 4. Eficiencia y escalado | 20 | Score del dev set vs. presupuesto (llamadas, tokens, runtime, intentos de verificación en paralelo); dónde se estanca la precisión y headroom restante | Genera la curva score-vs-tokens desde tus logs; marca mesetas |
| 5. Claridad y visuales | 15 | Escribir para un investigador de ML sin fondo civil/mecánico/eléctrico; hallazgo clave arriba; ≤2,000 palabras; las 3 figuras | Portada + diagrama + 2 gráficos de datos = requisito cumplido y puntos |
| **Total** | **100** | | |

### 5.3 Etapa 2 — evaluación en 56 tareas ocultas

1. El evaluador clona tu commit, corre `install` una vez (build container `debian:bookworm`, 30 min, `/opt/harness` ≤2 GiB comprimido) y el smoke test (bind en ≤120 s, escribe un archivo de prueba, manda `done`).
2. Califica tus `artifacts/` commiteados en las 29 dev y **re-corre en vivo una muestra aleatoria del dev set**: fallar reproducibilidad o hard-codear salidas = descalificación.
3. En cada una de las 56 tareas ocultas (6 estructural, 9 civil, 18 eléctrica, 23 mecánica): contenedor aislado (2 CPUs, 4 GB RAM, `/opt/harness` read-only, 1 GB en `/tmp` y `$HOME`, **6 h por tarea**). Scripts de verificación chequean cálculos cuantitativos, geometrías CAD/IFC y restricciones; el juez LLM (**Claude Opus 5.5**) califica los entregables abiertos en escala 0.0–1.0. Tareas sin `done`/`error` o expiradas = 0.

**Ranking**: cada finalista corre **3 veces** las 56 tareas (168 corridas). El resultado usa la **frontera de Pareto rendimiento-costo** de la media de score y el costo medio (precios de lista de Model Garden: `cloud.google.com/model-garden/pricing` y `/partner-models/pricing`).
- Se premian los **top 3 sistemas rankeados por score medio** que estén en la frontera Pareto, con media ≥ **0.138**.
- La Etapa 1 es **solo** un filtro de calificación; el score del Writeup no entra al ranking final.
- **Desempates**: score del Writeup Etapa 1 → timestamp de submission más temprano en Kaggle.
- Los organizadores publican scores y costos de todos; reintentan automáticamente fallos del evaluador y rate limits/outages del endpoint patrocinado **sin penalización**; HTTP 400, crashes no recuperados y timeouts del agente sí penalizan.

---

## 6. Tracks e incentivos

**Único track: Main Track · $400,000 USD**

| Puesto | Premio |
|---|---:|
| 1º | $250,000 |
| 2º | $100,000 |
| 3º | $50,000 |

- No otorga puntos ni medallas de Kaggle; sin leaderboards públicos intermedios (formato hackathon: se determina por rúbrica del sitio).
- Los premios van a los sistemas ganadores según la rúbrica; los potenciales ganadores son notificados por email; la entrada ganadora se licencia (código Apache-2.0; Writeup y documentación CC BY 4.0).
- Reconocimiento adicional implícito: publicación pública de scores y costos de todos los sistemas de la Etapa 2; los Top 100 y sus Writeups quedan visibles en Kaggle.
- Reglas de elegibilidad: una cuenta Kaggle por persona (no múltiples cuentas); empleados/contratistas de Google y Kaggle pueden participar pero no ganar premios; máx. 5 personas por equipo; 18+; excluidas regiones sancionadas.

---

## 7. Agradecimientos y organización

**Anfitrión y patrocinador**
- Google LLC (1600 Amphitheatre Parkway, Mountain View, CA) — equipo **Google Cloud AI Research** y AI & Infrastructure. Anuncio en el blog de Google Cloud por Burak Gokturk (VP R&D), Rujun Han y George Lee (PM).

**Socio industrial**
- **Mercor**: red de ingenieros licenciados que crearon, validaron e intensificaron las tareas (44 expert-authored + validación total de las co-authored); entorno de ejecución construido sobre **Archipelago** (framework open-source de Mercor, Apache-2.0). Blog de lanzamiento: Michael Bennett, Ricardo Haegler Pilnik, Vaibhav Mittal.

**Socios académicos** (del sitio oficial)
- Jiajun Wu (Stanford) · Saining Xie (NYU Courant) · Ranjay Krishna (U. Washington) · Mohit Bansal (UNC Chapel Hill) · Yilun Du (Harvard) · Yunzhu Li (Columbia)

**Jueces de la competencia**
- Yufan Zhuang · Rujun Han · Arijit Ray · Chen-Yu Lee (Research Scientists, Google)

**Equipo central (autores del paper y de la competencia)**
- Rujun Han, Yufan Zhuang, Arijit Ray, Han Yu, Zhongying CuiZhu, George Lee, Yifei Ming, Binz Roy, Varun Sakalkar, Vishy Tirumalashetty, Burak Gokturk, Tomas Pfister, Chen-Yu Lee (Google Cloud AI Research / Google)
- Equipo Kaggle: Addison Howard, Paul Mooney

**Recursos oficiales**
- Sitio del benchmark y leaderboard: `ple-bench.com` (contacto: `ple-bench@google.com`)
- Repositorio: `github.com/google-research/ple` (Apache-2.0; *no es un producto oficialmente soportado de Google*)
- Dataset gated del dev set: `huggingface.co/datasets/google/physical-engineerings-last-exam` (tareas dev bajo CC BY 4.0; acceso bajo solicitud)
- Paper: `arxiv.org/abs/2610.30537`

---

## 8. Guía estratégica del participante

### 8.1 Quick start (comandos exactos)

```bash
# 0. Prerrequisitos: Docker (Desktop+WSL2 en Windows) y uv
uv tool install harbor==0.20.0 --with websockets   # corre las tareas dev

# 1. Dataset gated: acepta términos en HF y exporta tu token
export HF_TOKEN=<tu token de lectura HF>

# 2. Copia una muestra a su propio repo (fuera del clon de la competencia)
cp -r sample_submissions/pi-opus ../mi-harness && git -C ../mi-harness init -q

# 3. (Opcional) Proxy local para modelos google-cloud — requiere tu proyecto GCP (facturado)
gcloud auth application-default login
export VERTEXAI_PROJECT=<tu-gcp-project> MODEL_PROXY_KEY=$(openssl rand -hex 24)
kit/model_proxy/start.sh &        # → MODEL_PROXY_URL=http://localhost:4000

# 4. Build + modelo + listen + smoke (+ cancel con --cancel-test)
uv run python -m kit check ../mi-harness

# 5. Corre y califica el dev set; escribe artifacts/
uv run python eval/run.py ../mi-harness

# 6. Antes de enviar: commit único de todo + readiness check + push
git -C ../mi-harness add -A && git -C ../mi-harness commit -m "PLE harness submission"
uv run python -m kit check ../mi-harness          # debe terminar en "ready to submit"
```

Luego en Kaggle: pestaña **Writeups** → *New Writeup* → enlaza el repo en **Project Links** → SHA de 40 caracteres al inicio → Submit. (El registro directo en ple-bench.com está cerrado; todo entra por Writeups de Kaggle.)

### 8.2 Las 8 muestras oficiales (`sample_submissions/`)

| Carpeta | Harness | Modelo default | Qué demuestra | Cuándo usarla |
|---|---|---|---|---|
| `minimal` | Custom (Python) | gemini-3.8-flash | Harness completo más pequeño (<250 líneas): un solo loop de tool-calling | Base pedagógica; punto de partida para loops propios |
| `plan-verify` | Custom (Python) | claude-opus-5-5 | Loop de `minimal` dividido en planner/worker/verifier con presupuesto por paso | Cuando tus fallos sean de verificabilidad (restricciones duras) |
| `node-protocol` | Custom (JS) | claude-opus-5-5 | Habla el protocolo WebSocket directamente, sin `taskbridge.py` | Si dominas Node o quieres control total del protocolo |
| `custom-openai` | Custom (Python) | gpt-oss-120b | Harness de referencia completo: MCP, streaming, **compaction de contexto**, retries conscientes del deadline | La mejor base competitiva para loop propio |
| `local-model` | custom-openai | `openai-compatible/gpt-oss-120b` | El mismo harness sobre un modelo que tú sirves | Solo para corridas locales (no es envío aceptado) |
| `hermes-opus` | Hermes Agent v0.22.2 | claude-opus-5-5 | Envuelve un agente existente cuyo terminal corre dentro del task container (plugin backend) | Prototipado rápido con agente ajeno |
| `pi-opus` | Pi 1.1.0 | claude-opus-5-5 | Envuelve un agente de coding con extensión TS que redirige file/shell al task container | Ídem; Pi no usa MCP (va por shell) |
| `agy-gemini` | Antigravity CLI 1.4.10 | gemini-3.8-flash | Envuelve un CLI cerrado vía MCP; **solo modelos Gemini** | Si tu estrategia es Gemini |

Todas piden el máximo nivel de razonamiento (`max` Claude/GLM — y GPT-6/DeepSeek-V4 en las custom; `high` Gemini y demás) vía variables (`AGY_EFFORT`, `THINKING`, `REASONING_EFFORT` en `env:`). `MAX_OUTPUT_TOKENS` default 32,000 (bájalo para modelos de contexto pequeño). **Regla de oro: genera tus `artifacts/` con el mismo `model_api` que envías.**

### 8.3 Alternativas gratuitas para tu setup (Gemini API + Kaggle GPU)

**Principio general**: no necesitas pagar nada para participar. La evaluación oficial es gratis (Google inyecta las claves) y no se exige cuenta de facturación de Google Cloud para el dev local: "puedes correr experimentos locales y generar `artifacts/` con cualquier modelo open-weight autoalojado o API/suscripción personal". El pago solo aparecería si quieres probar los modelos `google-cloud/*` en local con `kit/model_proxy` (facturado a tu proyecto Vertex) — prescindible.

**Opción A — Gemini API (free tier) como modelo de desarrollo:**
1. Clave en `--env-file` (fuera de la entrada) y `model_api` local tipo `gemini/...` u `openai-compatible/` con `model_base_url` para correr el kit y `eval/run.py`.
2. **Gestiona las cuotas** (límites por minuto/día del free tier): corre el dev set por subconjuntos (`eval/run.py ../mi-harness --tasks <id>`), itera con un modelo flash (tokens bajos) y reserva el modelo fuerte para evals clave; usa caching agresivo en tu loop.
3. **Juez gratis**: fija `JUDGE_MODEL` a Gemini (o a tu modelo open-weight) y decláralo en el Writeup; el organizador re-califica `artifacts/` con el juez oficial, así que tu juez local no afecta el ranking.
4. *Nota*: las entradas que usan modelo propio no son aceptadas como submission — al commitear, cambia `model_api` al `google-cloud/<id>` objetivo (permitido si lo documentas).

**Opción B — Kaggle GPU como servidor de modelo open-weight:**
1. En un notebook de Kaggle (GPU gratis, cuota ~30 h/semana), sirve un modelo open-weight de la lista con un endpoint **OpenAI-compatible** (p. ej. vLLM/llama.cpp): Gemma 4 26B A4B o gpt-oss-120b cuantizado caben en 16–24 GB de VRAM.
2. Expón el endpoint con un túnel (ngrok/cloudflared) y apunta `model_base_url` desde tu PC: el kit corre con Docker en tu máquina Windows y el modelo vive en la GPU de Kaggle.
3. El kit y `eval/run.py` requieren Docker **local** (no corren dentro de Kaggle): Docker Desktop + WSL2 es el prerrequisito de tu PC.

**Bonus directo en la rúbrica (criterio #3, 15 pts)**: tu setup natural compara **Gemini (familia Gemini, vía API)** vs. **open-weight (familia abierta, vía Kaggle)** — exactamente la comparación entre familias que pide el criterio, sin costo.

**Recomendación de ruta** (con tu infraestructura): empezar con Gemini free tier para el loop y las iteraciones (día 1–2), añadir el endpoint open-weight de Kaggle para la comparación cruzada y el juez alternativo (día 3+), y reservar los experimentos con `google-cloud/claude-opus-5-5` para... ningún momento obligatorio: tu entrada final puede apuntar a cualquier modelo patrocinado; elige el que tus datos dev muestran mejor en el Pareto (los 8 corren gratis en la Etapa 2 oficial).

### 8.4 Errores comunes y solución (del troubleshooting oficial)

| Síntoma | Solución |
|---|---|
| Tarea dev cuenta 0: *missing/refused* | Re-corre con `eval/run.py --tasks <id>` y valida con `kit artifacts` |
| "the harness changed after these artifacts were made" | Re-corre el dev set con el harness actualizado y commitea todo junto (`git add -A`) |
| Build falló | Revisa `build.log` en `~/.cache/plebench/<name>/` y corrige `install` |
| Smoke: el servidor nunca escuchó | Bind en `0.0.0.0:$PORT` (no `127.0.0.1`) en ≤120 s; dependencias bajo `/opt/harness`, invoca binarios por ruta completa |
| Smoke: connection refused / 403 | El serve solo alcanza el endpoint del modelo: elimina llamadas a otros hosts y usa `HTTPS_PROXY` en tu cliente HTTP |
| Smoke: 401 del modelo | Usa la clave inyectada por el evaluador, no una hardcodeada |
| `socket closed`, `AgentTimeoutError` | Manda `done` antes de `agent_timeout_sec`; stream de llamadas largas y presupuesto por paso |
| Score bajo completando la corrida | Verifica rutas y nombres **exactos** de entregables del enunciado; resumen claro en `done.final_message` |

### 8.5 Checklist pre-envío

- [ ] `kit check` termina en **ready to submit** (todas las etapas: yaml, files, build, model, listen, smoke, artifacts; `--cancel-test` también)
- [ ] `eval/run.py` completó el dev set con entregables en las rutas esperadas; `kit artifacts` acepta la `artifacts/` commiteada
- [ ] Todo en **un commit** (código + `submission.yaml` + `artifacts/`); `submission.yaml` con `model_api` = `google-cloud/<id>` objetivo
- [ ] Repo con licencia Apache-2.0 o MIT; ≤1 GiB de historia; artifacts sin comprimir ≤512 MiB / 10k archivos
- [ ] Repo público al cierre (o app ple-submission instalada si fue privado)
- [ ] Writeup ≤2,000 palabras: 5 criterios + portada + 3 figuras + SHA al inicio + repo en Project Links
- [ ] Juez local declarado en el Writeup (si no usaste un modelo frontera para calificar)
- [ ] Comparación ≥2 modelos con tabla en el Writeup (criterio #3)
- [ ] Envío confirmado en Kaggle antes del 5-ene-2027 23:59 UTC (puedes des-enviar, editar y re-enviar hasta el deadline)

### 8.6 Cronología

| Fecha (23:59 UTC salvo indique lo contrario) | Hito |
|---|---|
| 9-nov-2026 | Inicio de la competencia |
| 5-ene-2027 | **Deadline final**: Writeups y repos con `artifacts/` commiteados |
| 19-ene-2027 | Fin del juicio de Writeups Etapa 1 → Top 100 a Etapa 2 |
| 26-ene-2027 | Fin de evaluación del test set y **ganadores anunciados** |

Los organizadores se reservan el derecho de actualizar el cronograma.

---

## 9. Referencias y enlaces

- Páginas de la competencia (Kaggle):
  - `kaggle.com/competitions/physical-engineerings-last-exam/overview/description`
  - `kaggle.com/competitions/physical-engineerings-last-exam/overview/submission-requirements` (reglas de envío)
  - `kaggle.com/competitions/physical-engineerings-last-exam/overview/tracks-and-awards`
  - `kaggle.com/competitions/physical-engineerings-last-exam/overview/acknowledgements` (agradecimientos, jueces, cronología, cita)
  - `kaggle.com/competitions/physical-engineerings-last-exam/overview/evaluation` (rúbrica completa, modelos patrocinados, cómo enviar)
  - `kaggle.com/competitions/physical-engineerings-last-exam/rules` (reglas legales)
- Sitio del benchmark: `ple-bench.com` · Guía: `ple-bench.com/competition/guide` · Instrucciones para coding agents: `ple-bench.com/competition/agents`
- Repositorio: `github.com/google-research/ple` (README, `kit/`, `eval/`, `docs/protocol.md`, `docs/artifacts.md`, `docs/models.md`, `sample_submissions/README.md`)
- Dataset: `huggingface.co/datasets/google/physical-engineerings-last-exam`
- Paper: `arxiv.org/abs/2610.30537` (v2, 30-oct-2026)
- Blogs de lanzamiento: Google Cloud (`cloud.google.com/blog/products/ai-machine-learning/introducing-physical-engineerings-last-exam-for-agents`) y Mercor (`mercor.com/blog/introducing-physical-engineering-s-last-exam-ple-with-google-cloud-ai-research`)
- Precios de referencia para el cálculo de costo: `cloud.google.com/model-garden/pricing` y `cloud.google.com/model-garden/partner-models/pricing`

**Cita del benchmark** (si lo usas en investigación):

```bibtex
@misc{han2026ple,
  title         = {{PLE}: Physical-Engineering's Last Exam},
  author        = {Rujun Han and Yufan Zhuang and Arijit Ray and Han Yu and
                   Zhongying CuiZhu and George Lee and Yifei Ming and Binz Roy and
                   Varun Sakalkar and Vishy Tirumalashetty and Burak Gokturk and
                   Tomas Pfister and Chen-Yu Lee},
  year          = {2026},
  eprint        = {2610.30537},
  archivePrefix = {arXiv},
  primaryClass  = {cs.AI},
  url           = {https://arxiv.org/abs/2610.30537}
}
```

**Cita de la competencia (Kaggle)**:

```
Rujun Han, Yufan Zhuang, Arijit Ray, Han Yu, Zhongying CuiZhu, George Lee, Yifei Ming,
Binz Roy, Varun Sakalkar, Vishy Tirumalashetty, Addison Howard, Paul Mooney, Burak Gokturk,
Tomas Pfister, y Chen-Yu Lee. Google - Agent Harness on Physical-Engineering's Last Exam.
kaggle.com/competitions/physical-engineerings-last-exam, 2026. Kaggle.
```
