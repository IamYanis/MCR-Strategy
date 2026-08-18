# MCR Strategy — Project Status

## Objectif

Construire progressivement une stratégie quantitative de marché robuste,
tout en développant une infrastructure Python propre pour :

- télécharger les données ;
- créer des signaux ;
- backtester les stratégies ;
- construire des portefeuilles ;
- mesurer rendement et risque ;
- tester la robustesse ;
- intégrer turnover et coûts de transaction.

---

## Architecture actuelle

mcr-strategy/

- data/
  - raw/
- research/
  - notebooks/
    - explore_sp500.py
    - compare_trend_windows.py
    - compare_trend_periods.py
    - compare_markets.py
    - compare_portfolios.py
    - compare_trend_buffers.py
    - compare_buffer_portfolios.py
- src/
  - data/
    - download_sp500.py
    - download_markets.py
  - signals/
    - trend.py
  - portfolio/
    - backtest.py
    - dynamic_portfolio.py
  - risk/
    - metrics.py

---

## Données utilisées

Marchés actuellement téléchargés :

- S&P 500
- Nasdaq
- Euro Stoxx 50
- US Treasuries
- Gold
- Oil
- US Dollar Index
- US 3-Month Treasury rate pour le cash

Les fichiers CSV sont stockés dans :

data/raw/

Ils ne sont pas envoyés sur GitHub grâce au .gitignore.

---

## Premier signal étudié

Trend following basé sur moyenne mobile 200 jours.

Signal initial :

- investi si Close > MA200
- cash sinon

Pour éviter le look-ahead bias, le signal est décalé d'un jour avant
d'être utilisé comme position.

---

## Robustesse de la moyenne mobile

Fenêtres testées :

- MA50
- MA100
- MA150
- MA200
- MA250

Les horizons longs, principalement MA200 et MA250, ont montré un comportement
plus robuste que les horizons courts.

L'objectif n'est PAS de chercher une moyenne mobile optimale au jour près.

---

## Résultats MA200 sur le S&P 500

Sur l'historique utilisé :

Buy & Hold :

- CAGR : ~6.46 %
- Volatilité : ~19.25 %
- Sharpe : ~0.42
- Max Drawdown : ~-56.78 %

MA200 :

- CAGR : ~5.58 %
- Volatilité : ~10.67 %
- Sharpe : ~0.56
- Max Drawdown : ~-21.31 %

Conclusion :

MA200 sacrifie une partie du rendement mais réduit fortement le risque
et les drawdowns.

---

## Test multi-assets

Le signal MA200 a été testé sur :

- S&P 500
- Nasdaq
- Europe
- Treasuries
- Gold
- Oil
- USD

Résultat important :

Le trend following semble surtout utile comme mécanisme de contrôle du risque,
mais son efficacité varie selon les marchés.

Attention :

Les futures comme CL=F (Oil) ne doivent pas être interprétés comme un simple
Buy & Hold classique. Leur gestion nécessitera plus tard un moteur futures
plus réaliste.

---

## Portefeuille multi-assets

Actifs actuellement utilisés dans le portefeuille :

- S&P 500
- Nasdaq
- Europe
- Treasuries
- Gold
- USD

Oil est laissé de côté pour le moment.

### Buy & Hold équipondéré

- CAGR : ~6.56 %
- Volatilité : ~9.58 %
- Sharpe : ~0.73
- Max Drawdown : ~-28.12 %

### Trend MA200 + Cash

- CAGR : ~5.49 %
- Volatilité : ~6.00 %
- Sharpe : ~0.95
- Max Drawdown : ~-9.32 %

### Trend MA200 Redistributed

- CAGR : ~7.98 %
- Volatilité : ~9.96 %
- Sharpe : ~0.84
- Max Drawdown : ~-14.77 %

---

## Contrôle de concentration

Des caps de poids ont été testés :

### Cap 30 %

- CAGR : ~7.27 %
- Volatilité : ~8.70 %
- Sharpe : ~0.88
- Max Drawdown : ~-12.53 %

### Cap 40 %

- CAGR : ~7.56 %
- Volatilité : ~9.22 %
- Sharpe : ~0.86
- Max Drawdown : ~-13.53 %

### Cap 50 %

- CAGR : ~7.85 %
- Volatilité : ~9.55 %
- Sharpe : ~0.86
- Max Drawdown : ~-14.77 %

Le cap 30 % est actuellement une variante intéressante car il limite
la concentration tout en conservant un bon rendement.

---

## Problème identifié : whipsaw

Le signal MA200 classique change trop souvent lorsque les prix oscillent
autour de la moyenne mobile.

Sur la période commune du portefeuille :

- environ 870 changements de signal ;
- environ 40 jours/an avec au moins un changement.

Cela générait un turnover élevé.

---

## Solution étudiée : buffer autour de MA200

Une fonction avec hystérésis a été ajoutée.

Avec buffer 2 % :

- entrée lorsque Close > MA200 × 1.02
- sortie lorsque Close < MA200 × 0.98
- entre les deux : conservation de la position précédente

Résultats sur les changements de signal :

- buffer 0 % : 870 changements sur la période commune
- buffer 1 % : 316 changements
- buffer 2 % : 202 changements

---

## Configuration de travail actuelle

La variante actuellement la plus intéressante à poursuivre est :

- Trend MA200
- Buffer : 2 %
- Cap par actif : 30 %
- Cash rémunéré avec proxy 3-month Treasury
- Portefeuille multi-assets

IMPORTANT :

Ce n'est PAS considéré comme une stratégie finale ou optimale.

C'est seulement la meilleure version de travail actuelle.

---

## Résultats avec coûts de transaction

### Buffer 0 %

Turnover annuel : ~1035 %

Avec 10 bps :

- CAGR : ~6.20 %
- Sharpe : ~0.76
- Max Drawdown : ~-14.27 %

### Buffer 1 %

Turnover annuel : ~402 %

Avec 10 bps :

- CAGR : ~6.89 %
- Sharpe : ~0.83
- Max Drawdown : ~-13.75 %

### Buffer 2 %

Turnover annuel : ~254 %

Sans coûts :

- CAGR : ~7.42 %
- Volatilité : ~8.80 %
- Sharpe : ~0.88
- Max Drawdown : ~-11.88 %

Avec 10 bps :

- CAGR : ~7.16 %
- Sharpe : ~0.85
- Max Drawdown : ~-11.99 %

Avec 20 bps :

- CAGR : ~6.90 %
- Sharpe : ~0.83
- Max Drawdown : ~-12.10 %

Le buffer 2 % réduit fortement le turnover sans dégrader les performances.

---

## Limites actuelles du backtest

Le modèle est encore expérimental.

À améliorer :

- vraie dérive des poids entre rebalancements ;
- modèle plus réaliste du cash ;
- coûts spécifiques par instrument ;
- slippage ;
- ETF vs indices ;
- futures et roll ;
- dividendes ;
- qualité / survivorship des données ;
- tests out-of-sample ;
- tests par régime ;
- diversification plus large ;
- sizing par volatilité ;
- gestion du risque portefeuille.

Il faut éviter l'overfitting.

Ne PAS rechercher mécaniquement :

- MA exacte optimale ;
- buffer exact optimal ;
- cap exact optimal.

On cherche des zones de paramètres robustes.

---

## Prochaine étape prévue

Tester la configuration :

MA200 + buffer 2 % + cap 30 %

sur plusieurs sous-périodes historiques avec coûts de transaction inclus.

Objectif :

vérifier si les performances restent cohérentes dans plusieurs régimes
de marché et ne proviennent pas uniquement d'une période particulière.

---

## Commandes utiles

Activer l'environnement Python :

source .venv/bin/activate

Télécharger les données :

python -m src.data.download_markets

Analyse S&P 500 :

python -m research.notebooks.explore_sp500

Comparer les horizons MA :

python -m research.notebooks.compare_trend_windows

Comparer les périodes :

python -m research.notebooks.compare_trend_periods

Comparer les marchés :

python -m research.notebooks.compare_markets

Comparer les portefeuilles :

python -m research.notebooks.compare_portfolios

Comparer les buffers :

python -m research.notebooks.compare_trend_buffers

Tester buffers + turnover + coûts :

python -m research.notebooks.compare_buffer_portfolios