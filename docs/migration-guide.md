# Transition from OCA v1 to QLX

<p align="justify">
The OCA v1 model was the original version of the project, designed with a hardcoded, rigid structure for data querying and organization. As the needs for flexibility and scalability grew, the limitations of OCA v1 became apparent. This led to the development of the QLX model, which introduces a dynamic, Xvar-centered approach to data representation, making it more adaptable and suitable for complex, multi-dimensional queries.
</p>

| Feature               | OCA v1                                   | QLX v2                                     |
|-----------------------|------------------------------------------|--------------------------------------------|
| **Model Flexibility** | Hardcoded attributes and structure       | Fully dynamic, based on Xvars and catalogs |
| **Customization**     | Limited customization                    | High customization with Xvar catalogs      |
| **Querying Capabilities** | Simple, static filters              | Flexible, multi-dimensional querying       |
| **Catalog System**    | Non-existent                             | Comprehensive catalog system by dimensions |
| **Observatory Scope** | No observatory structure                | Scoped observatories with catalog constraints |
| **Extendability**     | Rigid, requires code changes            | Easily extended by adding new Xvars        |



### QLX Model

The **QLX** model, previously referred to as **OCA v2**, redefines the data structure around the concept of **Xvars** (variable attributes), **catalogs**, and **observatories**. The entire system is now built to be modular, flexible, and adaptable to new requirements without the need for code changes.

#### Key Innovations in QLX

1. **Xvars as Core Building Blocks**
    - In QLX, all product attributes are defined as **Xvars**, which are flexible, modular variables that represent different dimensions (spatial, temporal, interest, observable, info, and product type).
    - This approach allows new attributes to be added simply by creating new Xvars, without changing the underlying code.

2. **Dynamic Catalog System**
    - QLX introduces a powerful **catalog system** that organizes Xvars into collections by dimension. Each catalog contains Xvars for a specific type, such as spatial, temporal, interest, observable, info, or product type.
    - This catalog system allows for standardized attribute validation, flexible filtering, and easy extension. Users can create new catalogs or modify existing ones, dynamically changing the filtering options in the UI.

3. **Observatories for Scoped Querying**
    - The concept of an **Observatory** is central to QLX, providing a scoped environment where users can query products based on specific catalog constraints.
    - Each observatory includes a unique combination of catalogs, which defines the types of Xvars that can be used in that context. This allows for focused and relevant queries within specific data contexts, such as “Health Observatory for Mexico” or “Environmental Data for Urban Areas.”
    - Observatories allow data to be compartmentalized and queried in isolated contexts, which was not possible in OCA v1.

4. **Multi-Dimensional Querying**
    - The QLX  model supports complex, multi-dimensional querying across all catalog types. Users can filter data by combining spatial, temporal, interest, and observable variables, allowing for advanced data exploration.
    - The dynamic nature of Xvars and catalogs enables queries that adapt to the data context. For instance, filtering by “Mortality Rate” (observable) and “Age Group” (interest) is straightforward, as both are defined in catalogs and can be flexibly combined.

5. **Enhanced Extensibility**
    - QLX is designed for extensibility, with no need to modify the codebase when adding new data dimensions. New Xvars or catalogs can be introduced without impacting the system’s functionality.
    - This modularity ensures that QLX  can scale to accommodate new data sources, observatories, and attribute types, making it suitable for evolving data environments.
