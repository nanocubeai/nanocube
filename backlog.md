# Cubed Pandas Backlog

## Release 0.2.x (Current Scope of Work)

- [ ] Sampling for all column types - see function body 'sample' in class Context.

- [ ] to_df_code() - Creates a code snippet to recreate the current context with plain Pandas.

- [ ] Full Rework Time intelligence to support more complex time intelligence, e.g.:
  A dedicated parser/interpreter is required to support more complex time intelligence. like
  - [ ] actual day, week, month, quarter, year, hour, minute, second
  - [ ] `ytd`, `qtd`, `mtd`, `wtd`, `yoy`, `qoq`, `mom`, `wow`, `yoy`, `qoq`, `mom`, `wow`, `yoy`, `qoq`, `mom`, `wow`
  - [ ] 'last 2 days', 'next 3 months', 'last 4 quarters', 'next 5 weeks', 'last 6 years', 'next 7 days'
  - [ ] 'last Monday', 'next Tuesday', 'last Wednesday', 'next Thursday', 'last Friday', 'next Saturday', 'last Sunday'
  - [ ] 'on Monday', 'on Tuesday', 'on Wednesday', 'on Thursday', 'on Friday', 'on Saturday', 'on Sunday'
  - [ ] 'last Monday to last Friday', 'next Tuesday to next Saturday', 'last Wednesday to last Sunday'
  - [ ] 'last January', 'next February', 'last March', 'next April', 'last May', 'next June', 'last July', ...

- [ ] Treat int columns with typical ID or code names as dimension columns.
- [ ] Rewrite documentation based on new syntax
- [ ] Slice to support and resolve boolean operations to define row and colum dimensions in a single step.
  e.g. `trucks.slice(rows=c.salesrep & c.customer, columns=c.lastmonth & c.actualmonth)`
- [ ] Support callable function to filter Context objects, e.g. `cdf.product.filter(lambda x: x.startswith("A"))`.
- [ ] Collect real-world data sets for testing and validation and implement an automated tester for any dataframe.
 
## Release 0.3.x

- [ ] `address` property to return the fully qualified address to rebuild the full context from that address.
- [ ] add individual behaviours for key-errors per dimension into schema
- [ ] Extend Expression Parser to support basic filtering and mathematical operations on `Context` objects.

## Future Releases

Just ideas, neither decided, nore scheduled or prioritized.

- [ ] Support for **Linked Cubes** to mimic DWH-style star-schemas.
- [ ] **Custom Business Logic**: Allow users to define custom business logic for measures.
- [ ] **Custom Measures**: Allow users to define custom measures.
- [ ] **Custom Dimensions**: Allow users to define custom *calculated* dimensions.
- [ ] **Custom Members**: Allow users to define custom *calculated* members.

# Implemented Features, Issue, Bugs

## Release 0.2.x
- [x] Date,time and Datetime resolvers for **Englisch keywords** like `yesterday`, `today`, `tomorrow`, `lastweek`,
  `thisweek`, `nextweek`, `lastmonth`, `thismonth`, `nextmonth`, `lastyear`, `thisyear`, `nextyear` etc.
  as members of a dimension. Multiple words should either be written together or separated by `_`,
  e.g. `last_month` vs. `lastmonth`.
- [x] All member related functions should return a list of the member keys as defined in the dataframe.
  Not wrapped into a `Member` object.
- [x] Support for `in` operator on DimensionContext
- [x] add feature/switch to return None vs. 0 for data without records.
- [x] `true` & `false` as members of a dimension should be resolved as `True` and `False` respectively.
  Aliases to be supported `yes` & `no` and `on` & `off` and `1` & `0` if used via index.
- [x] Support callable methods for all aggregation functions, e.g. `sum` -> `sum()`.
  see https://stackoverflow.com/questions/20120983/determine-if-getattr-is-method-or-attribute-call
- [x] Further Cleanup and rewrite for Cube, Dimension and Measure object.
  Move all none essential methods, properties and settings to respective properties,
  e.g. `Cube.settings`, `Cube.properties`, `Cube.methods` etc.
- [x] check string representations for all objects when in running in Jupyter
- [x] Check, adapt and activate the existing writeback functionality.
- [x] Implement `cdf.product.members` property to return a list of all members for a dimension.
- [x] `top(n)` and `bottom(n)` functions for dimensions, e.g. `cdf.product.top(2)`.
- [x] `count` property for dimensions, e.g. `cdf.Online.product.count`, to count the number of distinct members.
  The current implementation counts the records for the default measure.
- [x] Implement `Context.full_address` property returning a dictionary.
- [x] ~~implement 'by(rows, colums)' feature for `Context` objects to mimic GroupBy functionality over 2 axis.~~
- [x] Boolean logic for `Contex` objects for advanced filtering. `and` and `or` operators 
      for `Context` objects,`and` as default.
- [x] Allow to set the default measure 
- [x] Filter functions for dimensions: include, exclude, filter, like, regex, etc.
- [x] Filter functions for measures: gt, lt, eq, ne, etc.
- [x] Data Type Validation for columns
- [x] Update/rewrite all tests based on new syntax


