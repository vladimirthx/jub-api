
 

The **QLX Model** organizes data using a natural metaphor, where **products** are represented as **seeds** with specific characteristics (Xvars), which are indexed (planted) in a structured space known as the **soil**. This conceptual model helps illustrate how products, categorized by their Xvars, can be efficiently queried using a **query tree** structure. By following this model, the QLX system allows dynamic and multi-dimensional querying based on combinations of attributes.

## Key Concepts

### 1. Seeds (Products with Xvars)

- In this model, each **product** is a **seed** containing a unique combination of **Xvars** (attributes) that describe its characteristics across multiple dimensions, such as spatial, temporal, demographic, and measurable metrics.

- A product’s Xvars define its essential attributes (e.g., "Country = MX", "Year = 2020", "Age = 18-65") that place it within a specific category in the **soil**.

- When a product is indexed (planted) in the soil, it becomes accessible for querying. Multiple products can share the same set of Xvars, forming the same **query tree** when queried.

<div style ="text-align: center;">
<img src="/images/seed.png" width=240>
</div>

### 2. Soil (Catalog Space)

- <p align="justify"> The **soil** represents the **catalog space**, where products (seeds) are organized and categorized based on their Xvars. Each cell in the soil symbolizes a grouping of products based on catalog-defined Xvar constraints.</p>

- <p align="justify">Catalogs serve as the rules that determine which Xvars (attributes) can be used for each dimension, ensuring that products are indexed in consistent, organized groups.</p>

- <p align="justify">Each Xvar dimension (e.g., spatial, temporal) has its catalog constraints, which help categorize products in the soil by predefined attributes. For example, the spatial catalog might limit Xvars to certain countries or states, while the temporal catalog restricts dates or time ranges.</p>

<div style ="text-align: center;">
<img src="/images/soil_catalogspace.png" width=240>
</div>


### 3. Query Tree

- The **query tree** represents the structure of a query as it searches through the soil, filtering products based on their Xvars.

- When a query is executed, it creates a tree-like structure that starts at the root and branches out to different Xvar conditions. Each level of the tree corresponds to a different Xvar dimension (e.g., spatial, then temporal, then interest).

- Nodes in the query tree represent checks for specific Xvar conditions (e.g., filtering by "Country = MX" or "State = SLP"), and branches follow the path of these conditions.

- Products that satisfy all conditions specified by the query reach the leaf nodes of the tree, representing the final result set.


<div style ="text-align: center;">
<img src="/images/trees.png" width=350>
</div>


### Process Flow

1. **Seeding Products with Xvars**:

    - Each product is represented as a **seed** and assigned a specific combination of Xvars that describe it across various dimensions.
   
    - This combination of Xvars defines the product’s characteristics and enables it to be indexed in the **soil** (catalog space).

2. **Indexing Products in the Soil**:
   
    - Once a product is defined by its Xvars, it is **indexed** (planted) in the soil, meaning it is placed into the catalog space based on its Xvar values.
   
    - The soil organizes products by catalog-defined Xvar constraints, ensuring that they are grouped by relevant categories. This indexing process allows products to be later retrieved through queries.

3. **Query Execution via the Query Tree**:
   
    - When a query is initiated, it forms a **query tree** that traverses the soil, filtering products according to the specified Xvars.
   
    - Starting from the root, the query tree grows by branching out to different conditions. Each branch corresponds to a level of filtering based on an Xvar (e.g., first spatial, then temporal).
   
    - Products that match all specified Xvars travel through the branches and reach the leaves of the query tree, representing the query results.
   
    - Multiple products can form the same query tree structure if they share the same combination of Xvars, allowing for efficient and consistent filtering across similar products.

### Conceptual Summary

- **Seeds** (products with Xvars) represent each entity in the QLX model, with characteristics defined by their Xvar values.

- **Soil** (catalog space) organizes products by their Xvars, categorizing them based on catalog constraints across dimensions.

- The **query tree** enables multi-dimensional querying by traversing the soil, filtering products based on the conditions specified by the Xvars.

- Through this structure, the QLX Model enables flexible, dynamic querying, allowing users to retrieve products based on combinations of attributes that define each query tree path.

This conceptual model illustrates how the QLX system efficiently organizes and queries products by treating them as seeds planted in a structured catalog space, with the query tree acting as the pathway to retrieve relevant results.