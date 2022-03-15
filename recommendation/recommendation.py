## through popularity
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import joblib

import os


# %matplotlib inline
plt.style.use("ggplot")

import sklearn
from sklearn.decomposition import TruncatedSVD

from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score


def get_popular_products(ratings_dataset):
    popular_products = pd.DataFrame(ratings_dataset.groupby('id')['rating'].count())
    most_popular = popular_products.sort_values('rating', ascending=False).head(10)

    return most_popular

# rating history with SVD
def collborative_filtering(ratings_dataset, product):
    ratings_utility_matrix = ratings_dataset.pivot_table(values='rate', index='user', columns='product', fill_value=0)
    x = ratings_utility_matrix.T
    x1 = x

    SVD = TruncatedSVD(n_components=10)
    decomposed_matrix = SVD.fit_transform(x)

    correlation_matrix = np.corrcoef(decomposed_matrix)

    i = product
    product_names = list(x.index)
    product_id = product_names.index(i)
     
    correlation_product_ID = correlation_matrix[product_id]

    Recommend = list(x.index[correlation_product_ID > 0.90])
    Recommend.remove(i) 

    recommend = Recommend[0:3]

    return recommend

# clustering
# useful when no purchase history is received
def check(row, cluster, vectorizer, model):
    Y = vectorizer.transform([row['description']])
    prediction = model.predict(Y)
    if(prediction[0] == cluster):
        return row

def clustering(product_description, product_df):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print('base_dir::' + base_dir)

    model = joblib.load(base_dir + '/recommendation/recommendation')
    vectorizer = TfidfVectorizer(stop_words='english')
    x = vectorizer.fit_transform(product_df["description"])

    Y = vectorizer.transform([product_description])
    prediction = model.predict(Y)

    count = 1
    in_cluster = pd.DataFrame()

    for index, row in product_df.iterrows():
        checked = check(row, prediction[0], vectorizer, model)
        if checked is not None and in_cluster.shape[0] < 4:
            in_cluster = in_cluster.append(checked)
    


    return in_cluster['id'].to_list()



