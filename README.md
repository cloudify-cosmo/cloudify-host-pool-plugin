Cloudify Host-Pool Plugin
=========================

[![Circle CI](https://circleci.com/gh/cloudify-cosmo/cloudify-host-pool-plugin.svg?style=shield)](https://circleci.com/gh/cloudify-cosmo/cloudify-host-pool-plugin)
[![Build Status](https://travis-ci.org/cloudify-cosmo/cloudify-host-pool-plugin.svg?branch=master)](https://travis-ci.org/cloudify-cosmo/cloudify-host-pool-plugin)

Cloudify Host-Pool Plugin

## Usage

See [Host-Pool Plugin](http://getcloudify.org/guide/3.2/plugin-host-pool.html)


## Example

The following simplified blueprint shows how to allocate a host from the host pool service
using a tag filter to ensure only hosts with the *redhat* tag are used.

```yaml
tosca_definitions_version: cloudify_dsl_1_2

imports:
- http://www.getcloudify.org/spec/cloudify/3.3.1/types.yaml
- https://raw.githubusercontent.com/cloudify-cosmo/cloudify-host-pool-plugin/master/plugin.yaml

inputs:
  hostpool_svc_endpoint:
    type: string
    description: |
      Endpoint for the host-pool REST service
    default: http://192.168.1.100:8080

node_templates:
  host_from_pool:
    type: cloudify.hostpool.nodes.LinuxHost
    properties:
      filters:
        tags:
        - redhat
    interfaces:
      cloudify.interfaces.lifecycle:
        create:
          inputs:
            service_url: { get_input: hostpool_svc_endpoint }
        delete:
          inputs:
            service_url: { get_input: hostpool_svc_endpoint }
```


For official blueprint examples using this Cloudify plugin, please see [Cloudify Community Blueprints Examples](https://github.com/cloudify-community/blueprint-examples/).

## Cloudify node types

### cloudify.hostpool.nodes.Host
This is the base type for a hostpool host node.  This type is not usually
directly instanciated from but it provides the foundation for more
convenient node types (for Windows and Linux specifically).

**properties**
```yaml
os:
    description: |
        Host OS to search for
    type: string
    required: true
filters:
    description: |
        A dictionary of values to pass as filters
    type: cloudify.datatypes.hostpool.Filters
    required: false
```

**filters**

Filters are used to allocate hosts based on various parameters.  Currently, the only supported
filters are *os* (which is set for you based on node type) and *tags*, a user-defined list of
strings that can be associated with a host and used to filter by.

For instance, you could have a Linux host in the host pool service with the tags ```['ubuntu', 'nodejs']```
to indicate that it's an Ubuntu Linux host with Node.js pre-installed.  Then, in your blueprint, you
can set the *tags* part of the filter to either (or both) of those strings to ensure you're allocating
a host that fits your needs.


### cloudify.hostpool.nodes.LinuxHost
*derived_from: [cloudify.hostpool.nodes.Host](#cloudifyhostpoolnodeshost)*

This is the usable node type for allocating Linux hosts from the hostpool service.

**properties**

All properties of this node type are inherited from its derived type.  This node type
sets the inherited *os* property to *linux*.

### cloudify.hostpool.nodes.WindowsHost
*derived_from: [cloudify.hostpool.nodes.Host](#cloudifyhostpoolnodeshost)*

This is the usable node type for allocating Windows hosts from the hostpool service.

**properties**

All properties of this node type are inherited from its derived type.  This node type
sets the inherited *os* property to *windows*.
