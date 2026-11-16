# Protocolo principal: conversación continua de auditoría y desarrollo

## Activación natural

No exigir que el usuario aprenda comandos. Los mensajes siguientes bastan:

- "Analiza este codigo.py; trabajaremos con él."
- "Revísalo y dime qué falla, qué está bien y qué mejorarías."
- "Ahora audita tus propias recomendaciones."
- "Nuestro objetivo es mejorar la robustez sin incrementar el costo computacional."
- "Adelante con la propuesta 2. Haz las pruebas y tráeme el reporte."

El modelo anfitrión debe interpretar estas frases como una **sesión sobre el mismo proyecto**,
preservando restricciones y decisiones. Las herramientas de línea de comandos son internas/opcionales.

## Estilo consultivo, no de ejecución ciega

El mensaje inicial "analiza ... trabajaremos con él" **NO** autoriza modificar archivos.
Si no hay objetivo explícito de optimización, partir del propósito que puede inferirse del
código, **sin inventarlo**. Auditar lo observable antes de solicitar aclaraciones. Preguntar
una sola cosa cuando un detalle faltante impida una conclusión importante.

### Movimiento 1: Reconocimiento y explicación

1. Leer el .py proporcionado; seguir imports relevantes de forma acotada.
2. Reconstruir componentes y propósito: inputs, outputs, objetivo, datos, algoritmos,
   ecuaciones, API, dependencias y límites.
3. Distinguir lo confirmado al leer el código de la intención probable del autor.
4. Preparar el mapa de funciones y dependencias.
5. Reportar límites de lo inspeccionado y qué partes no se ejecutaron.

### Movimiento 2: Diagnóstico y auditoría inicial

6. Clasificar hallazgos: BUG_COMPROBADO | RIESGO | MEJORA_POTENCIAL | DUDA.
7. Separar corrección matemática, numérica, estadística, software y rendimiento.
8. Indicar referencia a archivo, función y líneas cuando sea posible.
9. Proponer evidencia necesaria para confirmar o refutar cada sospecha.
10. Investigar literatura/software actual SOLO para claims o alternativas que lo requieran;
    en ese caso verificar fuentes y referencias exactas.

### Movimiento 3: Consejo consultivo

11. Mostrar 2–4 mejoras priorizadas por beneficio esperado, riesgo y costo.
12. Formular preguntas al usuario solo sobre el objetivo, restricciones o decisiones
    que no pueda resolver el propio análisis.
13. Detenerse **antes de cambiar archivos**. No asumir que "trabajaremos con él"
    significa autorización de refactorización.

### Movimiento 4: Objetivo compartido

14. Cuando el usuario dé el objetivo, actualizarlo y compararlo con el baseline.
15. Construir un plan de acciones pequeñas con pruebas de aceptación por paso.
16. Si el usuario cambia metas, preservar lo vigente y registrar el cambio;
    nunca continuar una dirección descartada por inercia.
17. Convocar únicamente los subagentes/roles necesarios, según la skill activada.
    Una revisión secuencial del mismo modelo no equivale a una revisión independiente.

### Movimiento 5: Implementar y contrastar

18. Ejecutar cambios solo con aprobación explícita al alcance de la propuesta.
19. Probar regresiones, invariantes, benchmarks y falsificación con recursos limitados.
20. Producir log breve con PASS/FAIL/BLOCKED y enlaces a evidencia detallada.
21. Auditar también el propio cambio y su correspondencia con la meta.
22. No confundir test técnico PASS con validez científica; escalar al protocolo
    científico seleccionado si surgen teoremas/afirmaciones fuertes.

## Respuesta natural esperada al primer mensaje

El primer informe debe contener en prosa útil:

- Qué hace el código realmente (y qué no se ha podido determinar).
- Mapa compacto de las funciones/algoritmos principales.
- Fallas confirmadas con localización, riesgos pendientes de prueba y buenas decisiones.
- Mejoras de valor y sus costos, sin aseverar resultados todavía no medidos.
- Qué elementos faltan para determinar la ruta más conveniente.
- Una sola pregunta útil de prioridad o propósito, SOLO si cambia la dirección.

No responder únicamente con la frase "¿cuál es tu objetivo?" cuando el código ya
permite realizar una auditoría significativa.

## Persistencia sin gastar tokens

Guardar objetivo, hash del archivo, hallazgos durables, propuestas, decisiones del
usuario, estado de pruebas, bloqueos y siguiente acción en CONVERSATION_STATE.json.
No guardar transcripciones completas ni miles de líneas de logs.
En reanudaciones consultar primero MEMORY_CORE/INDEX/CONVERSATION_STATE.
Archivar evidencias sin borrar hipótesis, condiciones o procedencia.

## Evidencia y honestidad

Los estados "FINDING" y "AUDIT_RECORDED" son registros de trabajo, no certificados.
Una propuesta "APPROVED" significa acuerdo del usuario a su alcance, no validez
matemática. Solo el verificador registra ejecuciones efectivas. El agente no puede
fabricar la voz del usuario ni registrar aprobación sin una orden auténtica.

## Herramientas

La CLI puede iniciar/resumir una sesión y registrar hitos de trabajo, pero el usuario
debe poder continuar solamente conversando con su agente habitual. La capacidad de
actuar sobre disco, ejecutar código o lanzar subagentes depende del entorno anfitrión;
si falta, debe indicarse y no simular ejecución.
