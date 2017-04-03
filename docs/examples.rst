Examples
========


Basic Linux Host
----------------

The following is an example of using the host-pool-plugin node types.::

    tosca_definitions_version: cloudify_dsl_1_2

    imports:
      - http://www.getcloudify.org/spec/cloudify/3.3.1/types.yaml
      - https://raw.githubusercontent.com/cloudify-cosmo/cloudify-host-pool-plugin/1.4/plugin.yaml

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


Nodecellar
----------

A full example that installs the nodecellar application using this plugin is available
`here <https://github.com/cloudify-cosmo/cloudify-nodecellar-example/blob/master/host-pool-blueprint.yaml>`_
