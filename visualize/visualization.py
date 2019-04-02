from database.models import *
from sqlalchemy import func
import matplotlib.pyplot as plt
import numpy as np
import networkx as nx

session = Session()
env = 'seed_list_'

def sum(list):
    s = 0
    for el in list:
        s += el[1]
    return s

number_of_sites = session.query(Site).count()

number_of_pages = session.query(Page).count()

number_of_duplicates = session.query(Page).filter(Page.page_type_code == 'DUPLICATE').count()

pages_by_type = session.query(Page.page_type_code, func.count()).group_by(Page.page_type_code).all()

number_of_images = session.query(Image).count()

pages_with_images = session.query(Image.page_id, func.count()).group_by(Image.page_id).all()
average_number_of_images_per_page = round(sum(pages_with_images) / len(pages_with_images), 1)

binary_files_by_type = session.query(PageData.data_type_code, func.count()).group_by(PageData.data_type_code).all()

pages_with_binary_files = session.query(PageData.page_id, func.count()).group_by(PageData.page_id).all()
average_number_of_binary_files_per_page = round(sum(pages_with_binary_files) / len(pages_with_binary_files), 1)

sites_with_page = session.query(Page.site_id, func.count()).group_by(Page.site_id).all()
average_number_of_pages_per_site = round(sum(sites_with_page) / len(sites_with_page), 1)


print('Number of sites', number_of_sites)
print('Number of pages', number_of_pages)
print('Number of duplicates', number_of_duplicates)
print('Pages by type', pages_by_type)
print('Number of images', number_of_images)
print('Average number of images per page', average_number_of_images_per_page)
print('Binary files by type', binary_files_by_type)
print('Average number of binary files per page', average_number_of_binary_files_per_page)
print('Average number of pages per site', average_number_of_pages_per_site)

fig_pages_by_type = plt.figure(figsize=(14.0, 8.0))
labels = [x[0] for x in pages_by_type]
sizes = [x[1] for x in pages_by_type]
plt.pie(sizes, labels=labels, autopct='%1.1f%%')
plt.axis('equal')
fig_pages_by_type.suptitle('Pages by type')
fig_pages_by_type.show()
fig_pages_by_type.savefig(env + 'pages_by_type.png')

fig_binary_files_by_type = plt.figure(figsize=(14.0, 8.0))
labels = [x[0] for x in binary_files_by_type]
sizes = [x[1] for x in binary_files_by_type]
plt.pie(sizes, labels=labels, autopct='%1.1f%%')
plt.axis('equal')
fig_binary_files_by_type.suptitle('Binary files by type')
fig_binary_files_by_type.show()
fig_binary_files_by_type.savefig(env + 'binary_files_by_type.png')

fig_number_of = plt.figure(figsize=(14.0, 8.0))
height = [number_of_sites, number_of_pages, number_of_duplicates, number_of_images]
bars = (
    'Number of sites (' + str(number_of_sites) + ')',
    'Number of pages (' + str(number_of_pages) + ')',
    'Number of duplicates (' + str(number_of_duplicates) + ')',
    'Number of images (' + str(number_of_images) + ')')
y_pos = np.arange(len(bars))
plt.bar(y_pos, height)
plt.xticks(y_pos, bars)
fig_number_of.suptitle('Analytics')
fig_number_of.savefig(env + 'analytics.png')

fig_binary_files_by_type = plt.figure(figsize=(14.0, 8.0))
labels = [x[0] for x in binary_files_by_type]
sizes = [x[1] for x in binary_files_by_type]
plt.pie(sizes, labels=labels, autopct='%1.1f%%')
plt.axis('equal')
fig_binary_files_by_type.suptitle('Binary files by type')
fig_binary_files_by_type.show()
fig_binary_files_by_type.savefig(env + 'binary_files_by_type.png')

fig_average_number_of = plt.figure(figsize=(14.0, 8.0))
height = [average_number_of_images_per_page, average_number_of_binary_files_per_page, average_number_of_pages_per_site]
bars = (
    'Average number of images per page (' + str(average_number_of_images_per_page) + ')',
    'Average number of binary files per page (' + str(average_number_of_binary_files_per_page) + ')',
    'Average number of pages per site (' + str(average_number_of_pages_per_site) + ')'
    )
y_pos = np.arange(len(bars))
plt.bar(y_pos, height)
plt.xticks(y_pos, bars)
fig_average_number_of.suptitle('Average analytics')
fig_average_number_of.savefig(env + 'average_analytics.png')

fig_network = plt.figure(figsize=(14.0, 8.0))
nodes = session.query(Link.from_page).group_by(Link.from_page).order_by(Link.from_page).all()
nodes = list(map(lambda x: x[0], nodes))

G=nx.Graph()
G.add_nodes_from(nodes)

edges = session.query(Link.from_page, Link.to_page).all()
G.add_edges_from(edges)

pos = nx.spring_layout(G)

nx.draw_networkx_nodes(G, pos, node_size=5, cmap=plt.cm.RdYlBu)
nx.draw_networkx_edges(G, pos, alpha=0.3)
plt.axis('off')
fig_network.suptitle('Network')
fig_network.savefig(env + 'network.png')
plt.show(G)