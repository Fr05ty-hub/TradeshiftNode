
# TradeshiftNode

Coding Challenge for Tradeshift

  

Amazing Co's need to model how their company is structured because they do awesome stuff

  

Welcome to a study on how to make node trees in Redis!

  

------------------------------------------------------

  

Each Node is a single hash with properties:

- "id"

- "height"

- "parent"

- "root"

  

Each Node also has another object which holds its own list of children. To avoid you the hassle of manually adding hashes and managing their children lists, I created an API call for it:

CALL TYPE: POST request

Address: localhost:5000/app/api/v1.0/nodes/add

Expected:

It expects a JSON file with the following properties as a minimum:

'id'

'parent'

'root'

More properties can be added, but the parent node must exist. Height is automatically added to the new node

Security:

HTTP requests to add or modify properties require Basic Authorisation:

user = 'test'

password = 'test'

  

To get a node's children:

CALL TYPE: GET request

Address: localhost:5000/app/api/v1.0/nodes/children/\<node>

It will return a JSON object with the list of children of \<node>

Security: NONE

  

To get descendants of a node:

CALL TYPE: GET request

Address: localhost:5000/app/api/v1.0/nodes/offspring/\<node>/\<levels>

It will return a JSON object with lists of descendants of \<node> up to the \<level> specified, with each list corresponding to a level of descendants

Security: NONE

  

To change the parent of a node:

CALL TYPE: PUT request

Address: localhost:5000/app/api/v1.0/nodes/parent_change

Expected:

A JSON file with the following properties:

'node' : '\<node>'

'new_parent' : 'id of node which will become the new parent of \<node>'

It will return an array for the amount of cascading changes it has done to its descendants if it executes properly, if it can't find the specified nodes, it will return an error

Security:

HTTP requests to add or modify properties require Basic Authorisation:

user = 'test'

password = 'test'
# TradeshiftNode

Coding Challenge for Tradeshift

  

Amazing Co's need to model how their company is structured because they do awesome stuff

  

Welcome to a study on how to make node trees in Redis!

  

------------------------------------------------------

  

Each Node is a single hash with properties:

- "id"

- "height"

- "parent"

- "root"

  

Each Node also has another object which holds its own list of children. To avoid you the hassle of manually adding hashes and managing their children lists, I created an API call for it:

CALL TYPE: POST request

Address: localhost:5000/app/api/v1.0/nodes/add

Expected:

It expects a JSON file with the following properties as a minimum:

'id'

'parent'

'root'

More properties can be added, but the parent node must exist. Height is automatically added to the new node

Security:

HTTP requests to add or modify properties require Basic Authorisation:

user = 'test'

password = 'test'

  

To get a node's children:

CALL TYPE: GET request

Address: localhost:5000/app/api/v1.0/nodes/children/\<node>

It will return a JSON object with the list of children of \<node>

Security: NONE

  

To get descendants of a node:

CALL TYPE: GET request

Address: localhost:5000/app/api/v1.0/nodes/offspring/\<node>/\<levels>

It will return a JSON object with lists of descendants of \<node> up to the \<level> specified, with each list corresponding to a level of descendants

Security: NONE

  

To change the parent of a node:

CALL TYPE: PUT request

Address: localhost:5000/app/api/v1.0/nodes/parent_change

Expected:

A JSON file with the following properties:

'node' : '\<node>'

'new_parent' : 'id of node which will become the new parent of \<node>'

It will return an array for the amount of cascading changes it has done to its descendants if it executes properly, if it can't find the specified nodes, it will return an error

Security:

HTTP requests to add or modify properties require Basic Authorisation:

user = 'test'

password = 'test'