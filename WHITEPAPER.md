# Catrina Engine vFinal+  
## Discrete Visual Alignment Engine for Proportional Fonts

**Autor:** Alfonso / TerraUniversalis  
**Fecha:** Abril 2026

---

## Resumen Ejecutivo
Catrina Engine vFinal+ es un sistema de **alineación visual discreta** diseñado para producir tablas de texto perfectamente alineadas en **fuentes proporcionales** (Twitter/X, WhatsApp, Telegram, clientes móviles y web), donde los métodos tradicionales basados en longitud (`len()`) o tipografía monoespaciada fallan.

A diferencia de una “fórmula”, Catrina es un **motor metrológico perceptual** compuesto por:
- un modelo aproximado de ancho visual,
- un optimizador discreto de padding,
- perfiles específicos por plataforma,
- y un lazo explícito de **calibración humana**.

El resultado no es una alineación tipográfica absoluta (matemáticamente imposible en texto plano), sino una alineación **operativamente perfecta**, estable y reproducible en cada plataforma.

---

## 1. El Problema Real

Las plataformas sociales modernas usan **fuentes proporcionales**:
- los caracteres tienen anchos distintos (`1` ≠ `8` ≠ `.`),
- existe *kerning* (ajustes entre pares de letras),
- los emojis son glifos de ancho variable,
- y cada plataforma (SO, app, navegador) renderiza distinto.

Por ello:
- `len()` **no representa ancho visual**,
- el alineado clásico de columnas se rompe,
- y no existe una solución universal sin acceso al motor gráfico.

---

## 2. Límite Teórico

Es **imposible** lograr alineación matemática perfecta de texto plano **cross‑platform** debido a:
- subpixel rendering,
- hinting de fuentes,
- fallback tipográfico,
- zoom y escalado del sistema.

Catrina Engine acepta explícitamente este límite y trabaja *hasta el borde máximo de lo posible*.

---

## 3. Principios de Diseño

1. **Alineación perceptual, no tipográfica.**  
   El ojo humano valida el resultado, no un valor en píxeles.

2. **Discretización visible.**  
   El padding se hace con caracteres visibles (`:`, `.` y espacios), no con control invisible.

3. **Optimización por error mínimo.**  
   El relleno se elige para minimizar el error visual residual.

4. **Perfiles por plataforma.**  
   No existe un set universal de pesos.

5. **Humano en el loop.**  
   La calibración visual es parte formal del sistema.

---

## 4. Arquitectura del Sistema

### 4.1 Componentes

**Catrina Engine**
- cálculo de ancho visual por *grapheme cluster*,
- optimizador discreto de padding (`best_fill()`),
- generador de filas alineadas.

**Platform Profile**
- mapa de anchos por carácter,
- ancho de emoji,
- ancho de separador `|`,
- parámetros de penalización y offset,
- target visual de columna.

**Calibration Pack**
- generación de múltiples candidatos,
- selección visual humana,
- refinamiento adaptativo.

---

## 5. Grapheme Clusters (Unicode)

Catrina no mide *codepoints*, sino **grapheme clusters** (UAX #29): lo que el usuario percibe como “un carácter”.

Esto permite manejar correctamente:
- emojis compuestos por ZWJ (`👨‍👩‍👧‍👦`),
- banderas (`🇲🇽`),
- variaciones de tono de piel,
- combinaciones con VS‑16.

Cada grapheme se trata como **una unidad visual**, con un ancho asignado.

---

## 6. Optimización Discreta del Relleno

El alineado no usa redondeos simples.

Para un delta de ancho a cubrir:
- se prueban combinaciones discretas de relleno (`:` + `.` o espacios),
- se evalúa el error absoluto,
- se penaliza suavemente el *overshoot*,
- se elige la combinación visualmente más cercana.

Esto evita deriva acumulada y oscilaciones.

---

## 7. Targets de Columna

El objetivo de alineación puede definirse de dos formas:

1. **Por texto ancla** (ej. `XRP::::::::::::`) validado visualmente.
2. **Por ancho numérico almacenado**, independiente del texto.

La versión vFinal+ recomienda **guardar el target numérico** tras calibración para evitar inestabilidad cuando cambian pesos.

---

## 8. Calibración Visual (Formalizada)

### 8.1 Por qué es necesaria

Sin acceso a métricas reales de render, la calibración debe ser **humana**.

### 8.2 Proceso

1. El sistema genera un **paquete de 9 candidatos** (A–I) variando:
   - ancho de `:`,
   - ancho de espacio,
   - ancho de emoji,
   - ancho de `|`,
   - offset de target.

2. El usuario **copia y pega** el bloque completo en la plataforma destino.
3. Selecciona el candidato que *se ve recto*.
4. (Opcional) Se ejecuta un **refinamiento adaptativo** alrededor del elegido.
5. El perfil se guarda como preset de plataforma.

La calibración es reproducible, explícita y auditable.

---

## 9. Error Residual

El sistema acepta un error residual típico **< 2 px**, imperceptible en feeds reales.

Este error:
- no acumula,
- es estable,
- y es dominado por variaciones de fuente, no por el motor.

---

## 10. Qué NO Hace Catrina (por diseño)

- No promete alineación matemática universal.
- No mide píxeles.
- No depende de hacks invisibles.
- No introduce kerning artificial agresivo.

La estabilidad prima sobre la ilusión de exactitud.

---

## 11. Casos de Uso

- Tablas financieras en X / WhatsApp.
- Rankings cripto, bursátiles, deportivos.
- Reportes técnicos compartidos en chat.
- Outputs de LLM listos para redes.

---

## 12. Definición Formal

**Catrina Engine vFinal+**  
> *Discrete Visual Alignment Engine = (Aproximación Tipográfica) + (Optimización Discreta) + (Perfil de Plataforma) + (Calibración Humana)*

---

## 13. Conclusión

Catrina no intenta violar los límites de la tipografía digital.

Los **reconoce, los formaliza y los convierte en un sistema operativo usable**.

No es una fórmula.

Es un **instrumento tipográfico de precisión perceptual**.

---

© 2026 — TerraUniversalis / Alfonso
