# Inferred low- and medium-voltage distribution grid models for Switzerland
Welcome to our repository, where we share our inferred geo-referenced models of Switzerland's low- and medium-voltage power distribution grids (PDGs). These models were obtained using the framework introduced by [A. Oneto et. al](to appear in TechRxiv), and stem from the meticulous analysis of publicly available data on power demand and transport infrastructure. With 792 medium-voltage grids and 34,920 low-voltage grids, our dataset represents all of Switzerland's power distribution landscape. We invite you to harness this rich dataset to explore, analyze, and contribute to a deeper understanding of large-scale power distribution systems.
## Files provided
The dataset has two main folders with medium-voltage (MV) and low-voltage (LV) grids. All the PDGs are described by two geojson files: a nodes file and an edges file. These geojson files can be read by software such as ArcGIS and QGIS, with which you can easily visualize all the components and their attributes. Moreover, you can read this data as GeoDataFrame using Python GeoPandas. For instance, if you have two files named 'nodes.geojson' and 'edges.geojson', you can access their information with the following code:
```python
import geopandas as gpd
nodes_gdf, edges_gdf = gpd.read_file('nodes.geojson'), gpd.read_file('edges.geojson')
```
In addition, the MV and LV folders have the following content:
- LV: there are nine subfolders inside, which contain the following number of grids,
  
| Urbanization type | Alps   | Jura  | Midlands  |
| :---         |    :---        |          :--- |          :--- |
| Periurban   | 2038   | 551    | 3510    |
| Rural     | 8264       | 1178      | 3323      |
| Urban     | 5316       | 375      | 10365      |

Note that an edge and a node file define every grid. Hence, in the cases when node files do not have a matching edge file, it means that these demand nodes are then connected to the MV infrastructure. For more detail, check Section 3 of [A. Oneto et. al].
- MV: 792 grids.
## References
For a detailed description of the framework through which the data was generated, please go to 

[A. Oneto, B. Gjorgiev, F. Tettamanti, and G.Sansavini “Large-Scale Inference of Geo-Referenced Power Distribution Grids Using Open Data”, to appear in TechRxiv.]
