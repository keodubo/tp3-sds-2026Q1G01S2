# Presentacion Beamer del TP3

Deck LaTeX/Beamer para `Sistema 1`, basado en los artefactos existentes de:

- `artifacts/system1/studies/inciso-1.1`

## Build

```bash
./presentation/system1-beamer/build.sh
```

El script:

1. Regenera los PNG para slides en `presentation/system1-beamer/assets/generated/`.
2. Compila `deck.tex`.
3. Compila `guion-defensa.tex`.
4. Deja los PDFs finales en:
   - `presentation/system1-beamer/system1-beamer.pdf`
   - `presentation/system1-beamer/guion-defensa.pdf`

## Placeholders pendientes

- portada: nombres, emails, legajos y grupo
- links de YouTube/Vimeo en la slide de animaciones
- still de `N=1000` si en el futuro aparece `runs/runtime_n_1000_seed_100.txt`

## Material adicional

- `guion-defensa.tex`: explicaci\'on de implementaci\'on, guion oral slide por slide, preguntas/respuestas y checklist para defensa en vivo.
