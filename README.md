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

Note that an edge and a node file define every grid. Hence, in the cases when node files do not have a matching edge file, it means that these demand nodes are then connected to the MV infrastructure. For more detail, check Section 3 of [A. Oneto et. al](to appear in TechRxiv).
- MV: 792 grids.

## Detailed description of the data files

The geometries of the geojson files are in the EPSG:2056 projection.

### MV files

All the MV grids operate at 20 kV with 25 MVA 110/20 kV transformers. For more details about the transformer, go [here](https://pandapower.readthedocs.io/en/v2.6.0/std_types/basic.html#transformers).

The line types are shown below. For more details, go [here](https://pandapower.readthedocs.io/en/v2.6.0/std_types/basic.html#lines). 

Overhead lines (OHL)

| Line type ID | Model |
|    :---        |     :---        | 
| 1 |  48-AL1/8-ST1A 20.0       |
| 2 |  94-AL1/15-ST1A 20.0      |
| 3 | 122-AL1/20-ST1A 20.0      |
| 4 |  243-AL1/39-ST1A 20.0     |
| 5 |  2x122-AL1/20-ST1A 20.0   |
| 6  |  2x243-AL1/39-ST1A 20.0   |
        
Underground cables (CS)

| Line type ID | Model |
|    :---        |     :---        | 
| 1 | NA2XS2Y 1x70 RM/25 12/20 kV |
| 2 | NA2XS2Y 1x185 RM/25 12/20 kV |
| 3 | NA2XS2Y 1x240 RM/25 12/20 kV |
| 4  | NA2XS2Y 2x150 RM/25 12/20 kV |
| 5  | NA2XS2Y 2x240 RM/25 12/20 kV  |
| 6  | NA2XS2Y 4x150 RM/25 12/20 kV  |

Note that OHL 5 and 6, and CS 4, 5, and 6, are custom lines, that are defined for modeling purposes, as they allow us to place more than one line in a given edge geometry.

**Nodes**

- osmid: unique identifier for each node in the grid.
- x: east-west coordinate.
- y: north-south coordinate.
- el_dmd: active power demand in MW.
- lv_grid: the unique identifier of the MV/LV transformer connection. If the value is -1, the node is either an MV consumer or a node with no power demand.
- consumers: True if there is power consumption in the node, False otherwise.
- label: has two kinds of entries: 1) an identifier from OSM data in case the node was retrieved from that database, or 2) a string ‘intersect_X’, which identifies the projection of a load to its closest street point. 
- source: True if the node corresponds to the transformer location. False otherwise.
- voltage: The resulting voltage in p.u. from a steady state AC power flow analysis.
- geometry: Point objects used to map the nodes with GIS tools.

**Edges**

- u: the osmid of the start node of the edge.
- v: the osmid of the end node of the edge.
- key: all 0. This is used to define a MultiGraph, since the OSMnx library provides useful functions for processing street data, and works with MultiGraph.
- length: the length of the edge in km.
- OHL: True if the line is an overhead line. False if it is an underground cable.
- x: reactance of the line in Ohms.
- r: resistance of the line in Ohms.
- b: shunt susceptance in Siemens.
- s_nom: upper bound of the apparent power in the line, in MVA.
- line_type: identifier of the line type in the catalog. This identifier is used to access the type in the CS and OHL catalog, e.g., if the line type is 1 and the line is OHL, we should access the catalog of OHL in the identifier 1.
- load: the ratio of apparent power transferred in the line with s_nom in the steady state AC power flow analysis.

### LV files

All the LV grids operate at 400 V. The supplying transformer of the grid depends on its urbanization type as indicated in the table below. For more details about the transformers, go [here](https://pandapower.readthedocs.io/en/v2.6.0/std_types/basic.html#transformers).

| Urbanization type | Transformer type   |
| :---         |    :---        | 
| Periurban & Urban   | 20/0.4 kV 630 kVA  |
| Rural     | 20/0.4 kV 250 kVA    |

The line types are shown below. For more details, go [here](https://pandapower.readthedocs.io/en/v2.6.0/std_types/basic.html#lines). 

| Urbanization type | Model   |
| :---         |    :---        | 
| Urban   | NAYY4x240SE |
| Periurban & Rural     | NAYY4x150SE |

**Nodes**

- osmid: unique identifier for each node in the grid.
- x: east-west coordinate.
- y: north-south coordinate.
- el_dmd: active power demand in MW.
- Category: the type of grid, e.g., ‘Midlands-Urban’.
- consumers: True if there is power consumption in the node, False otherwise.
- label: has two kinds of entries: 1) an identifier from OSM data in case the node was retrieved from that database, or 2) a string ‘intersect_X’, which identifies the projection of a load to its closest street point. 
- source: True if the node corresponds to the transformer location. False otherwise.
- voltage: The resulting voltage in p.u. from a steady state AC power flow analysis.
- geometry: Point objects used to map the nodes with GIS tools.

**Edges**

- u: the osmid of the start node of the edge.
- v: the osmid of the end node of the edge.
- key: all 0. This is used to define a MultiGraph, since the OSMnx library provides useful functions for processing street data, and works with MultiGraph.
- length: the length of the edge in km.
- x: reactance of the line in Ohms.
- r: resistance of the line in Ohms.
- b: shunt susceptance in Siemens.
- s_nom: upper bound of the apparent power in the line, in MVA.
- line_type: number of cables that are placed in the given edge geometry. 
- load: the ratio of apparent power transferred in the line with s_nom in the steady state AC power flow analysis.

## References
For a detailed description of the framework through which the data was generated, please go to 

[A. Oneto, B. Gjorgiev, F. Tettamanti, and G.Sansavini “Large-Scale Inference of Geo-Referenced Power Distribution Grids Using Open Data”, to appear in TechRxiv.]
