# French birth rates 2019, visualized

This is a homework for the visualization course,
part of my master's course at the Paris-Saclay University.

## Run locally

As this work includes plotly and Dash visualizations, 
it is necessary to run the code locally to access all the functionalities.

Here's how to do it:
1. Clone the repository
   ```
   git clone https://github.com/LilianBoulard/FrenchBirthRates2019
   cd FrenchBirthRates2019
   ```
2. Create a new python environment, for example with conda
   ```
   conda create --name frbrates2019 python=3.10
   conda activate frbrates2019
   pip install -r requirements.txt
   ```
3. Launch the Jupyter Notebook
   ```
   jupyter notebook birth_insee.ipynb
   ```
4. Launch the dashboard
   ```
   python dashboard.py
   ```

5. Once done, clean up
   ```
   conda deactivate
   conda env remove -n frbrates2019
   ```