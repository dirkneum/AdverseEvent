import glob
import json
import sys

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st


def field_value(f, fn):
    if fn not in f:
        return '-'
    if f[fn] == '':
        return '?'
    return f[fn]


@st.cache
def load_data(results=sys.maxsize, medicinalproduct_id=None):
    drugadministrationroute = []
    drugs = []
    medicinalproduct = []
    reactions = []
    reportercountry = []
    safetyreportid = []
    reactionmeddrapt = []

    for fn in glob.glob('drug-event*.json'):
        with open(fn, 'rt') as f:
            x = json.load(f)
            for i in range(len(x['results'])):
                result = x['results'][i]
                patient = result['patient']
                if medicinalproduct_id is not None and medicinalproduct_id not in [z['medicinalproduct'] for z in
                                                                                   patient['drug']]:
                    continue
                for drug in patient['drug']:
                    for reaction in patient['reaction']:
                        if field_value(drug, 'medicinalproduct') == medicinalproduct_id:
                            continue
                        drugadministrationroute.append(field_value(drug, 'drugadministrationroute'))
                        drugs.append(len(patient['drug']))
                        medicinalproduct.append(field_value(drug, 'medicinalproduct'))
                        reactions.append(len(patient['reaction']))
                        reportercountry.append(field_value(
                            result['primarysource'] if result['primarysource'] is not None else {},
                            'reportercountry'))
                        safetyreportid.append(field_value(result, 'safetyreportid'))
                        reactionmeddrapt.append(field_value(reaction, 'reactionmeddrapt'))
                if i >= results:
                    break
    return pd.DataFrame({'drugadministrationroute': drugadministrationroute,
                         'drugs': drugs,
                         'medicinalproduct': medicinalproduct,
                         'reactions': reactions,
                         'reactionmeddrapt': reactionmeddrapt,
                         'reportercountry': reportercountry,
                         'safetyreportid': safetyreportid})

results = int(st.text_input('Number of results', '1000'))

# load json into dataframe
df = load_data(results)

#
st.markdown('### Product by Reaction')
df2 = df.groupby(['medicinalproduct', 'reactionmeddrapt']).nunique(
    'safetyreportid').reset_index().sort_values('safetyreportid', ascending=False)
st.write(df2[:100])

# bar plot
st.markdown('### Reaction Frequency')
df2a = df.groupby(['reactionmeddrapt']).nunique('safetyreportid').reset_index().sort_values('safetyreportid',
                                                                                            ascending=False)
st.write(df2a)

fig, ax = plt.subplots()
sns.set(style="whitegrid")
g = sns.barplot(x="reactionmeddrapt", y="safetyreportid", data=df2a[:10])
g.set_xticklabels(g.get_xticklabels(), rotation=90)
# ax.set(xlabel='reactionmeddrapt', ylabel='Safety Report ID')
st.pyplot(fig)

#
st.markdown('### Product by Country')

reportercountries = df.groupby('reportercountry').nunique('safetyreportid').sort_values('safetyreportid',
                                                                                        ascending=False).reset_index()
reportercountry = st.selectbox('Select a country', reportercountries)

df3 = df[df['reportercountry'] == reportercountry].groupby(['medicinalproduct']).nunique(
    'safetyreportid').sort_values('safetyreportid', ascending=False).head(10).reset_index().dropna()
st.write(df3)

#
st.markdown('### Drugs Taken Together')

medicinalproducts = df.groupby('medicinalproduct').nunique('safetyreportid').sort_values('safetyreportid',
                                                                                         ascending=False).reset_index()
medicinalproduct = st.selectbox('Select a medicinal product', medicinalproducts)

df4 = load_data(results, medicinalproduct).groupby(['medicinalproduct']).nunique(
    'safetyreportid').reset_index().sort_values('safetyreportid', ascending=False)
st.write(df4)

min_drugs = st.slider('Minimum number of drugs', 0, 10)
df5 = df[df['drugs'] >= min_drugs].groupby(['reactionmeddrapt']).nunique('safetyreportid').reset_index().sort_values('safetyreportid', ascending=False)
st.write(df5)

fig, ax = plt.subplots()
g = sns.barplot(x="drugs", y="safetyreportid", data=df5)
g.set_xticklabels(g.get_xticklabels(), rotation=90)
st.pyplot(fig)
