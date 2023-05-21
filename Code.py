# -*- coding: utf-8 -*-
"""Anomaly_Detection.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1a2PfsmQwRgLlq0Z32U7yI4twi9J_B0I1

"""

!pip install opendatasets
import gzip
import opendatasets as od
#download given dataset for the original problem
od.download(
    "https://www.kaggle.com/datasets/galaxyh/kdd-cup-1999-data?resource=download")

import numpy as np
import random
import copy
from scipy.spatial.distance import cdist
import math
from sklearn.model_selection import train_test_split
import pandas as pd
from sklearn.preprocessing import LabelEncoder
np.set_printoptions(threshold=np.inf)

"""#Kmeans

##Classify Each Centroid
"""

def classify_centroid(centroids, data_cluster, training_labels):
  num_clusters = len(centroids)
  cluster_identification = np.zeros([num_clusters, 1])
  unique, counts = np.unique(data_cluster[:], return_counts=True)
  for j in range(len(unique)): 
    cluster_number = unique[j]
    cluster_sum = counts[j] 
    indices = np.where(data_cluster[:] == cluster_number)
    indices = np.array(indices)
    indices=indices[0,:]
    cluster_mask = np.zeros(data_cluster.shape[0])
    cluster_mask[indices] = 1
    ground_truth_clust = cluster_mask * training_labels
    unique_clust, counts_clust = np.unique(ground_truth_clust, return_counts=True)
    majority_count = -1
    majority_index = -1
    for k in range(len(unique_clust)):
      if unique_clust[k] > 0:
        if counts_clust[k] > majority_count:
          majority_count = counts_clust[k] 
          majority_index = unique_clust[k]
    cluster_identification[j] = majority_index  #Cluster identification to contain the class of the majority of the cluster
  return cluster_identification

"""##Assign each test sample to a centroid"""

def assign_centroids(testing_set, centroids, cluster_identification, label_list):
  cluster_index = []
  clustering_statistics = np.zeros([len(label_list)])
  euc_dist = cdist(testing_set, centroids, metric = 'euclidean')
  for i in range(len(testing_set)):
    min_index = np.argmin(euc_dist[i])
    cluster_index.append(min_index+1)
    clustering_statistics[int(cluster_identification[min_index]-1)] = clustering_statistics[int(cluster_identification[min_index]-1)] + 1
  return np.array(cluster_index).astype(int), clustering_statistics

"""##Remove empty clusters"""

def remove_empty_clusters(Data_Matrix, best_centroids, data_cluster):
  counts = np.zeros([len(best_centroids), 1])
  for i in range(len(data_cluster)):
    counts[int(data_cluster[i]-1), 0] = counts[int(data_cluster[i]-1), 0] + 1 
  len_centroids = 0
  for i in range(len(counts)):
    if counts[i] != 0:
      len_centroids = len_centroids + 1
  centroids_kmeans = np.zeros([len_centroids, best_centroids.shape[1]])
  c = 0
  for i in range(len(counts)):
    if counts[i] != 0:
      centroids_kmeans[c] = best_centroids[i]
      c = c+1
  
  # Get the euclidean distance between each record and the current centroids
  euc_dist = cdist(Data_Matrix, centroids_kmeans, metric = 'euclidean')
  # Cluster Assignment 
  for i in range(Data_Matrix.shape[0]):
    min_index = np.argmin(euc_dist[i])
    data_cluster[i] = min_index + 1

  return centroids_kmeans, data_cluster

"""##Kmeans function"""

def kmeans(Data_Matrix, k, max_iterations, threshold, rand_restart):
  min_sse = float('inf')
  best_clusters =  [[] for _ in range(k)]
  best_centroids = np.zeros([k, Data_Matrix.shape[1]])

  for r in range(rand_restart):
    data_size = len(Data_Matrix)
    centroids_indices = random.sample(range(data_size), k)
    centroids = [Data_Matrix[i] for i in centroids_indices]
    old_centroids = np.array(centroids).astype(float)
    new_centroids = np.array(centroids).astype(float)
    clusters = [[] for _ in range(k)]
    
    for m in range(max_iterations):
      # Get the euclidean distance between each record and the current centroids
      euc_dist = cdist(Data_Matrix, old_centroids, metric = 'euclidean')
      # Cluster Assignment 
      for i in range(data_size):
        min_index = np.argmin(euc_dist[i])
        clusters[min_index].append(i)
      sse_centroids = 0

      SSE = 0.0
      # Calculate SSE
      for i in range(k):
        for j in range(len(clusters[i])):
          SSE = SSE + euc_dist[clusters[i][j], i]
      if SSE < min_sse:
        min_sse = SSE
        best_clusters = copy.deepcopy(clusters)
        best_centroids = copy.deepcopy(old_centroids)
      # Centroid Update
      for i in range(k):
        if len(clusters[i]) != 0:
          new_centroids[i] = np.mean(Data_Matrix[clusters[i]], axis=0)
          sse_centroids = sse_centroids + np.linalg.norm(old_centroids[i] - new_centroids[i])**2
          old_centroids[i] = new_centroids[i]
      clusters = [[] for _ in range(k)]
      if sse_centroids <= threshold:
        break
  data_cluster = np.zeros([Data_Matrix.shape[0], 1])
  for i in range(k):
    for j in range(len(best_clusters[i])):
      data_cluster[best_clusters[i][j], 0] = i+1


  centroids_kmeans, data_cluster = remove_empty_clusters(Data_Matrix, best_centroids, data_cluster)

  return centroids_kmeans, data_cluster.astype(int)

"""#Normalized Cut

##Assignment statistics
"""

def assignment_statistics(data_cluster_Ncut, cluster_identification, label_list):
  clustering_statistics = np.zeros([len(label_list)])
  for i in range(len(data_cluster_Ncut)): 
    clustering_statistics[int(cluster_identification[data_cluster_Ncut[i]-1]-1)] = clustering_statistics[int(cluster_identification[data_cluster_Ncut[i]-1]-1)] + 1
  return clustering_statistics

"""##Normalized Cut function"""

def Normalized_cut(Data_matrix, k, nearest_K):
  similarity_matrix = np.zeros([Data_matrix.shape[0], Data_matrix.shape[0]])
  Degree_matrix = np.zeros([Data_matrix.shape[0], Data_matrix.shape[0]])
  euc_distance = cdist(Data_matrix, Data_matrix, metric='euclidean')

  for i in range(Data_matrix.shape[0]):
    sorted_distances = np.argsort(euc_distance[i])
    sorted_distances = sorted_distances[1:nearest_K+1]
    for j in range(len(sorted_distances)):
      similarity_matrix[i, sorted_distances[j]] = 1

  for i in range(Data_matrix.shape[0]):
    similarity_matrix[j, j] = 0
    Degree_matrix[i,i] = sum(similarity_matrix[i,:])
  similarity_matrix = similarity_matrix + similarity_matrix.transpose()

  L =  Degree_matrix - similarity_matrix
  Degree_inverse = np.linalg.inv(Degree_matrix)
  Norm_L = Degree_inverse @ L

  eig_values, eig_vectors = np.linalg.eig(Norm_L)
  # The imaginary part of the eigenvectors indicates the orientation of the vector in the complex plane.
  eig_values = np.real(eig_values)
  eig_vectors = np.real(eig_vectors)
  indices = eig_values.argsort()
  eig_values_vector = eig_values[indices]
  eig_vectors = eig_vectors[:,indices]
  # Normalization of the eigenvectors corresponding to the lowest k eigenvalue
  eig_vectors = eig_vectors[:, 0:k]
  for j in range(eig_vectors.shape[0]):
    norm = np.linalg.norm(eig_vectors[j])
    eig_vectors[j] = eig_vectors[j] / norm
  max_iterations = 30
  threshold = 0.01
  rand_restart = 5
  best_centroids, data_cluster = kmeans(eig_vectors, k, max_iterations, threshold, rand_restart)
  return best_centroids, data_cluster

"""#DBSCAN Clustring"""

def dbscan(data, eps, min_pts, num_clusters):
    # initialize visited and cluster labels
    visited = np.zeros(len(data), dtype=bool)
    cluster_labels = np.zeros(len(data), dtype=int)

    # find neighbors for each point
    neighbors = []
    for i in range(len(data)):
        dist = np.linalg.norm(data - data[i], axis=1)
        neighbors.append(np.where(dist <= eps)[0])

    # iterate over unvisited points
    cluster = 0
    for i in range(len(data)):
        if not visited[i]:
            visited[i] = True

            # find neighbors of current point
            current_neighbors = neighbors[i]

            # check if current point is a core point
            if len(current_neighbors) >= min_pts:
                cluster += 1
                cluster_labels[i] = cluster

                # expand cluster
                j = 0
                while j < len(current_neighbors):
                    neighbor = current_neighbors[j]
                    if not visited[neighbor]:
                        visited[neighbor] = True

                        # find neighbors of neighbor
                        neighbor_neighbors = neighbors[neighbor]

                        # check if neighbor is a core point
                        if len(neighbor_neighbors) >= min_pts:
                            # add neighbor's neighbors to current_neighbors
                            for nn in neighbor_neighbors:
                                if nn not in current_neighbors:
                                    current_neighbors = np.append(current_neighbors, nn)

                    # add neighbor to cluster
                    if cluster_labels[neighbor] == 0:
                        cluster_labels[neighbor] = cluster

                    j += 1

            # assign noise label to non-core point
            else:
                cluster_labels[i] = -1

    # assign remaining unassigned points to noise
    cluster_labels[cluster_labels == 0] = -1

    # assign points to desired number of clusters
    unique_labels = np.unique(cluster_labels)
    num_clusters_found = len(unique_labels) - 1  # exclude noise label
    while num_clusters_found > num_clusters:
        # find smallest cluster
        smallest_cluster_size = np.inf
        smallest_cluster_label = None
        for label in unique_labels:
            if label == -1:
                continue
            cluster_size = np.sum(cluster_labels == label)
            if cluster_size < smallest_cluster_size:
                smallest_cluster_size = cluster_size
                smallest_cluster_label = label

        # merge smallest cluster with nearest neighbor
        nearest_neighbor_dist = np.inf
        nearest_neighbor_label = None
        for label in unique_labels:
            if label == smallest_cluster_label or label == -1:
                continue
            dist = np.min(np.linalg.norm(data[cluster_labels == smallest_cluster_label] -
                                          data[cluster_labels == label], axis=1))
            if dist < nearest_neighbor_dist:
                nearest_neighbor_dist = dist
                nearest_neighbor_label = label

        cluster_labels[cluster_labels == smallest_cluster_label] = nearest_neighbor_label
        unique_labels = np.unique(cluster_labels)
        num_clusters_found = len(unique_labels) - 1  # exclude noise label

    # return cluster labels for each point
    return cluster_labels

"""#Agglomerative Clustering"""

def agglomerative_clustering(data, k):
    # initialize clusters
    clusters = [[i] for i in range(len(data))]
    # calculate distances between points
    euc_dist = cdist(data, data)
    # merge clusters until k clusters remain
    while len(clusters) > k:
        # find the closest clusters
        min_dist = np.inf
        for i in range(len(clusters)):
            for j in range(i+1, len(clusters)):
                # find the distance between the two clusters
                dist = 0
                for a in clusters[i]:
                    for b in clusters[j]:
                        dist += euc_dist[a][b]
                dist /= (len(clusters[i]) * len(clusters[j]))

                # update minimum distance and closest clusters
                if dist < min_dist:
                    min_dist = dist
                    closest_clusters = (i, j)

        # merge the closest clusters
        clusters[closest_clusters[0]] += clusters[closest_clusters[1]]
        del clusters[closest_clusters[1]]


    cluster_index_for_each_point = np.zeros(len(data))
    for u in range(len(clusters)):
      for t in range(len(clusters[u])):
        cluster_index_for_each_point [clusters[u][t]] = u
        
    # return the final clusters and cluster index for each point 
    return clusters,cluster_index_for_each_point

"""#Evaluation Functions

##Conditional Entropy
"""

def conditional_entropy(labels, ground_truth):
  unique, counts = np.unique(labels[:], return_counts=True)
  conditional_ent = 0
  for j in range(len(unique)): 
    cluster_number = unique [j]
    cluster_sum = counts[j] 
    indices = np.where(labels[:] == cluster_number)
    indices = np.array(indices)
    indices=indices[0,:]
    cluster_mask = np.zeros(labels.shape[0])
    cluster_mask[indices] = 1
    ground_truth_clust = cluster_mask * ground_truth
    unique_clust, counts_clust = np.unique(ground_truth_clust, return_counts=True)
    cond_ent_clust = 0
    for k in range(len(unique_clust)):
      if unique_clust[k] > 0:
        ent = (counts_clust[k] / cluster_sum) * math.log2(counts_clust[k] / cluster_sum)
        cond_ent_clust = cond_ent_clust + -1*ent
    conditional_ent = conditional_ent + (cluster_sum/labels.shape[0])*cond_ent_clust
  return conditional_ent

"""##Purity"""

def purity(labels, ground_truth):
  unique, counts = np.unique(labels[:], return_counts=True)
  purity = 0
  for j in range(len(unique)): 
    cluster_number = unique [j]
    cluster_sum = counts[j] 
    indices = np.where(labels[:] == cluster_number)
    indices = np.array(indices)
    indices=indices[0,:]
    cluster_mask = np.zeros(labels.shape[0])

    cluster_mask[indices] = 1
    ground_truth_clust =  cluster_mask * ground_truth  
    unique_clust, counts_clust = np.unique(ground_truth_clust, return_counts=True)
    majority = -1
    for k in range(len(unique_clust)):
      if unique_clust[k] > 0:
        if counts_clust[k] > majority:
          majority = counts_clust[k] 
    cluster_purity = majority / cluster_sum
    purity = purity + (cluster_sum/labels.shape[0])*cluster_purity 
  return purity

"""##F-Measure"""

def f_measure(labels, ground_truth):
  unique, counts = np.unique(labels[:], return_counts=True)
  sigma_f = 0
  clusters = len(unique)
  for j in range(len(unique)): 
    cluster_number = unique [j]
    cluster_sum = counts[j] 
    indices = np.where(labels[:] == cluster_number)
    indices = np.array(indices)
    indices=indices[0,:]
    cluster_mask = np.zeros(labels.shape[0])
    cluster_mask[indices] = 1
    ground_truth_clust = cluster_mask * ground_truth
    unique_clust, counts_clust = np.unique(ground_truth_clust, return_counts=True)
    majority = -1
    for k in range(len(unique_clust)):
      if unique_clust[k] > 0:
        if counts_clust[k] > majority:
          majority = counts_clust[k] 
          index = k
    prec = majority / cluster_sum
    total_occurence = np.count_nonzero(ground_truth == unique_clust[index])
    rec = majority / total_occurence
    F_measure = (2 * prec * rec) / (prec + rec)
    sigma_f = sigma_f + F_measure
  return (sigma_f/clusters)

"""##Pairwise Measures"""

def pairwise_measures(labels, ground_truth):
  unique, counts = np.unique(labels[:], return_counts=True)
  TP = 0
  FP = 0
  FN = 0
  TN = 0
  cluster_counts = []
  for j in range(len(unique)): 
    cluster_number = unique [j] 
    cluster_sum = counts[j] 
    indices = np.where(labels[:] == cluster_number)
    indices = np.array(indices)
    indices=indices[0,:]
    cluster_mask = np.zeros(labels.shape[0])
    cluster_mask[indices] = 1
    ground_truth_clust = cluster_mask * ground_truth
    unique_clust, counts_clust = np.unique(ground_truth_clust, return_counts=True)
    matrix = np.column_stack((unique_clust, counts_clust))
    for i in range(matrix.shape[0]):
      cluster_counts.append(matrix[i])

    FP_temp = 0
    for k in range(len(unique_clust)):
      if unique_clust[k] > 0:
        TP = TP + math.comb(counts_clust[k], 2)
        FP_temp = FP_temp + (counts_clust[k] * (cluster_sum - counts_clust[k]))

    FP = FP + FP_temp / 2

  cluster_counts = np.array(cluster_counts)
  for m in range (cluster_counts.shape[0]):
    if cluster_counts[m,0] > 0:
      for n in range  (cluster_counts.shape[0]):
        if cluster_counts[m,0] == cluster_counts[n,0] and m!=n:
          FN = FN + cluster_counts[m,1] * cluster_counts[n,1]
        if cluster_counts[m,0] != cluster_counts[n,0] and m!=n and cluster_counts[n,0] != 0:
          TN = TN + cluster_counts[m,1] * cluster_counts[n,1]
  FN = FN / 2
  TN = (TN / 2)- FP
  
  jacc = TP / (FN + TP + FP)
  rand = (TP + TN) / (FN + TN + TP + FP)
  return jacc, rand

"""##Beta CV"""

def beta_cv(Data_matrix, labels):
  unique, counts = np.unique(labels[:], return_counts=True)
  for i in range(len(unique)):
    labels = np.where(labels == unique[i], i+1, labels)
  unique, counts = np.unique(labels[:], return_counts=True)
  N_in = 0
  N_out = 0
  for i in range(len(counts)):
    N_in = N_in + math.comb(counts[i],2)
    for j in range(len(counts)):
      if i!=j:
        N_out = N_out + counts[i] * counts[j]
  N_out = N_out / 2
  proximity_matrix = np.zeros([len(unique), len(unique)])
  for i in range(sum(counts)):
    for j in range(sum(counts)):
      if labels[i] == labels[j] and i!=j:
        distance = np.linalg.norm(Data_matrix[i] - Data_matrix[j])
        proximity_matrix[int(labels[i]) - 1, int(labels[i]) - 1] += distance
      elif labels[i] != labels[j]:
        distance = np.linalg.norm(Data_matrix[i] - Data_matrix[j])
        proximity_matrix[int(labels[i]) - 1, int(labels[j]) - 1] += distance
        proximity_matrix[int(labels[j]) - 1, int(labels[i]) - 1] += distance
  W_in = np.trace(proximity_matrix) / 2
  W_out = (np.sum(proximity_matrix) - np.trace(proximity_matrix)) / 4

  BETACV = (W_in / N_in) / (W_out / N_out)
  return BETACV

"""##N_cut measure"""

def N_cut(Data_matrix, labels):
  unique, counts = np.unique(labels[:], return_counts=True)
  for i in range(len(unique)):
    labels = np.where(labels == unique[i], i+1, labels)
  unique, counts = np.unique(labels[:], return_counts=True)
  proximity_matrix = np.zeros([len(unique), len(unique)])
  for i in range(sum(counts)):
    for j in range(sum(counts)):
      if labels[i] == labels[j] and i!=j:
        distance = np.linalg.norm(Data_matrix[i] - Data_matrix[j])
        proximity_matrix[int(labels[i]) - 1, int(labels[i]) - 1] += distance
      elif labels[i] != labels[j]:
        distance = np.linalg.norm(Data_matrix[i] - Data_matrix[j])
        proximity_matrix[int(labels[i]) - 1, int(labels[j]) - 1] += distance
        proximity_matrix[int(labels[j]) - 1, int(labels[i]) - 1] += distance
  Ncut_measure = 0
  for i in range(len(counts)):
    Ncut_measure = Ncut_measure + (sum(proximity_matrix[i,:])- proximity_matrix[i,i]) / sum(proximity_matrix[i,:])

  return Ncut_measure

"""#Loading Dataset"""

def load(data_path, test_path, train_only):
  le = LabelEncoder()
  if train_only == True:
    df = pd.read_csv(data_path, compression='gzip', header=None)
    num_rows = df.shape[0]
  else: 
    df1 = pd.read_csv(data_path, compression='gzip', header=None)
    num_rows = df1.shape[0]
    df2 = pd.read_csv(test_path, compression='gzip', header=None)
    df = pd.concat([df1, df2], axis=0)
  # identify the categorical and numeric columns
  categorical_cols = [col for col in df.columns if df[col].dtype == 'object']
  categorical_cols = categorical_cols [:-1]
  numeric_cols = df.select_dtypes(include='number').columns.tolist()
  
  numeric_data = df.iloc[:, numeric_cols].values
  categorical_data = df.iloc[:, categorical_cols]

  # perform one-hot encoding on the categorical features except the label column
  one_hot_data = pd.get_dummies(categorical_data)

  # Apply label encoding to the label column
  df['col41_encoded'] = le.fit_transform(df[41])

  # Get the encoded label of the normal class
  label_list = []
  for label, encoded_label in zip(le.classes_, le.transform(le.classes_)):
      label_list.append(label[:-1])
  label_column = np.array(df['col41_encoded'])  # To make it an np array
  data = np.concatenate((numeric_data, one_hot_data), axis=1)
  for i in range(len(label_column)):
    label_column[i] = label_column[i] + 1 
  return data, label_column, label_list, num_rows

"""#Sample Runs

##Datasets for Kmeans
"""

test_path = '/content/kdd-cup-1999-data/corrected.gz'
training_path_kmeans = '/content/kdd-cup-1999-data/kddcup.data_10_percent.gz'
data_kmeans, labels_kmeans, label_list, num_rows = load(training_path_kmeans, test_path, False)
training_data_kmeans = data_kmeans[0:num_rows, :]
training_labels_kmeans = labels_kmeans[0:num_rows]
testing_data_kmeans = data_kmeans[num_rows:, :]
testing_labels_kmeans = labels_kmeans[num_rows:]

"""##Kmeans Sample Run"""

k = [7, 15, 23, 31, 45]
max_iterations = 10
threshold = 0.01
rand_restart = 5
print('K-MEANS')
for i in range(len(k)):
  print('For ', k[i], 'clusters: \n')
  centroids_Kmeans, data_cluster = kmeans(training_data_kmeans, k[i], max_iterations, threshold, rand_restart)
  cluster_identification = classify_centroid(centroids_Kmeans, data_cluster, training_labels_kmeans)
  cluster_labels, clustering_statistics = assign_centroids(testing_data_kmeans, centroids_Kmeans, cluster_identification, label_list)
  ground_truth = testing_labels_kmeans

  print('\tNORMAL TRAFFIC DETECTED:\t\t{} occurence\n'.format(int(clustering_statistics[label_list.index('normal')])))
  print('\tANOMALIES DETECTED: \n')
  for j in range(len(label_list)):
    if j != label_list.index('normal') and clustering_statistics[j] != 0:
      print('\n\t\t{} anomaly:\t{} occurence'.format(label_list[j], int(clustering_statistics[j])))

  print('\n\n\tEXTERNAL MEASURES: \n')
  print('\n\t\tPurity: ', purity(cluster_labels, testing_labels_kmeans))
  print('\n\t\tConditional Entropy:', conditional_entropy(cluster_labels, testing_labels_kmeans))
  print('\n\t\tF_measure: ', f_measure(cluster_labels, testing_labels_kmeans))
  jacc_Kmeans, rand_Kmeans = pairwise_measures(cluster_labels, testing_labels_kmeans)
  print('\n\t\tJaccard Index: ', jacc_Kmeans)
  print('\n\t\tRand Index: ', rand_Kmeans)
  print('\n\n')

# Not used due to its very high complexity O(n^2) where n denotes the number of testing points (311029 point)
print('\n\n\tINTERNAL MEASURES: \n')
print('\n\t\tBetaCV: ', beta_cv(testing_data_kmeans, cluster_labels))
print('\n\t\tNormalized Cut: ', N_cut(testing_data_kmeans, cluster_labels))

"""##Datasets for Spectral Clustering"""

training_path_ncut = '/content/kdd-cup-1999-data/kddcup.data.gz'
training_data_ncut, training_labels_ncut, label_list, num_rows= load(training_path_ncut, None,  True)

"""##Spectral Clustering Sample Run"""

training_data_ncut, _, training_labels_ncut, _ = train_test_split(training_data_ncut, training_labels_ncut, test_size=0.999, random_state=42, shuffle = True, stratify = training_labels_ncut)
NN_similarity_metric = 3
k_clusters = 23
centroids_Ncut, data_cluster_Ncut = Normalized_cut(training_data_ncut, k_clusters, NN_similarity_metric)
cluster_identification = classify_centroid(centroids_Ncut, data_cluster_Ncut, training_labels_ncut)
clustering_statistics = assignment_statistics(data_cluster_Ncut, cluster_identification, label_list)
print('NORMALIZED CUT\n')
print('\tNORMAL TRAFFIC DETECTED:\t\t{} occurence\n'.format(int(clustering_statistics[label_list.index('normal')])))
print('\tANOMALIES DETECTED: \n')
for j in range(len(label_list)):
  if j != label_list.index('normal') and clustering_statistics[j] != 0:
    print('\n\t\t{} anomaly:\t{} occurence'.format(label_list[j], int(clustering_statistics[j])))

print('\n\n\tEXTERNAL MEASURES: \n')
print('\n\t\tPurity: ', purity(data_cluster_Ncut, training_labels_ncut))
print('\n\t\tConditional Entropy:', conditional_entropy(data_cluster_Ncut, training_labels_ncut))
print('\n\t\tF_measure: ', f_measure(data_cluster_Ncut, training_labels_ncut))
jacc_ncut, rand_ncut = pairwise_measures(data_cluster_Ncut, training_labels_ncut)
print('\n\t\tJaccard Index: ', jacc_ncut)
print('\n\t\tRand Index: ', rand_ncut)
print('\n\n')
#######################################################################
# Compared to K-Means on the same data
max_iterations = 30
threshold = 0.01
rand_restart = 5
print('K-MEANS\n')
centroids_Kmeans, data_cluster = kmeans(training_data_ncut, k_clusters, max_iterations, threshold, rand_restart)
cluster_identification = classify_centroid(centroids_Kmeans, data_cluster, training_labels_ncut)
clustering_statistics = assignment_statistics(data_cluster_Ncut, cluster_identification, label_list)
ground_truth = training_labels_ncut
print('\tNORMAL TRAFFIC DETECTED:\t\t{} occurence\n'.format(int(clustering_statistics[label_list.index('normal')])))
print('\tANOMALIES DETECTED: \n')
for j in range(len(label_list)):
  if j != label_list.index('normal') and clustering_statistics[j] != 0:
    print('\n\t\t{} anomaly:\t{} occurence'.format(label_list[j], int(clustering_statistics[j])))

print('\n\n\tEXTERNAL MEASURES: \n')
print('\n\t\tPurity: ', purity(data_cluster, training_labels_ncut))
print('\n\t\tConditional Entropy:', conditional_entropy(data_cluster, training_labels_ncut))
print('\n\t\tF_measure: ', f_measure(data_cluster, training_labels_ncut))
jacc_Kmeans, rand_Kmeans = pairwise_measures(data_cluster, training_labels_ncut)
print('\n\t\tJaccard Index: ', jacc_Kmeans)
print('\n\t\tRand Index: ', rand_Kmeans)
print('\n\n')

"""##Datasets for DBSCAN Clustering"""

training_path_DB = '/content/kdd-cup-1999-data/kddcup.data.gz'
training_data_DB, training_labels_DB, label_list, num_rows= load(training_path_DB, None,  True)

"""##DBSCAN Clustring Sample Run"""

training_data_dbscan, _, training_labels_dbscan, _ = train_test_split(training_data_DB, training_labels_DB, test_size=0.999, random_state=42, shuffle = True, stratify = training_labels_DB)
k_clusters = 23
epsilon=8
min_per_cluster=20
labels = dbscan(training_data_dbscan, epsilon, min_per_cluster, k_clusters)
print('DBSCAN Clustring\n')
clusters_no_array = np.zeros(k_clusters)
cluster_identification = classify_centroid(clusters_no_array, labels, training_labels_dbscan)
int_array = labels.astype(int)
clustering_statistics = assignment_statistics(int_array, cluster_identification, label_list)
print('\tNORMAL TRAFFIC DETECTED:\t\t{} occurence\n'.format(int(clustering_statistics[label_list.index('normal')])))
print('\tANOMALIES DETECTED: \n')
for j in range(len(label_list)):
  if j != label_list.index('normal') and clustering_statistics[j] != 0:
    print('\n\t\t{} anomaly:\t{} occurence'.format(label_list[j], int(clustering_statistics[j])))
print('\n\n\tEXTERNAL MEASURES: \n')
print('\n\t\tPurity: ', purity(labels, training_labels_dbscan))
print('\n\t\tConditional Entropy:', conditional_entropy(labels, training_labels_dbscan))
print('\n\t\tF_measure: ', f_measure(labels, training_labels_dbscan))
jacc_ncut, rand_ncut = pairwise_measures(labels, training_labels_dbscan)
print('\n\t\tJaccard Index: ', jacc_ncut)
print('\n\t\tRand Index: ', rand_ncut)
print('\n\n')

"""##Datasets for Agglomerative Clustering"""

training_path_Agg = '/content/kdd-cup-1999-data/kddcup.data.gz'
training_data_Agg, training_labels_Agg, label_list, num_rows= load(training_path_Agg, None,  True)

"""##Agglomerative Clustring Sample Run"""

training_data_agg, _, training_labels_agg, _ = train_test_split(training_data_Agg, training_labels_Agg, test_size=0.9999, random_state=42, shuffle = True, stratify = training_labels_Agg)
k_clusters = 23
clusters,labels = agglomerative_clustering(training_data_agg, k_clusters)
print('AGGLOMERATIVE Clustring\n')
clusters_no_array = np.zeros(k_clusters)
cluster_identification = classify_centroid(clusters_no_array, labels, training_labels_agg)
int_array = labels.astype(int)
clustering_statistics = assignment_statistics(int_array, cluster_identification, label_list)
print('\tNORMAL TRAFFIC DETECTED:\t\t{} occurence\n'.format(int(clustering_statistics[label_list.index('normal')])))
print('\tANOMALIES DETECTED: \n')
for j in range(len(label_list)):
  if j != label_list.index('normal') and clustering_statistics[j] != 0:
    print('\n\t\t{} anomaly:\t{} occurence'.format(label_list[j], int(clustering_statistics[j])))
print('\n\n\tEXTERNAL MEASURES: \n')
print('\n\t\tPurity: ', purity(labels, training_labels_agg))
print('\n\t\tConditional Entropy:', conditional_entropy(labels, training_labels_agg))
print('\n\t\tF_measure: ', f_measure(labels, training_labels_agg))
jacc_ncut, rand_ncut = pairwise_measures(labels, training_labels_agg)
print('\n\t\tJaccard Index: ', jacc_ncut)
print('\n\t\tRand Index: ', rand_ncut)
print('\n\n')
