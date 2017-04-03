Types
=====

When the plugin is requested to provision a host,
it will make a request to the Host-Pool-Service,
which will in turn look for available matching hosts inside the pool,
and assign one to that request.

The same flow is executed when the plugin is requested to release that host.
The pool of available hosts will be determined at the time of the Host-Pool-Service installation,
as explained below.


Node Types
----------

.. cfy:node:: cloudify.hostpool.nodes.Host

    Base type for a pool host.

**Note that you must provide the service_url of the host pool service as an input to the lifecycle operations.**

**Attributes:**

  * ``ip`` the private ip of the host.
  * ``user`` the username of the host.
  * ``port`` the authentication port of this host.
  * ``public_address`` the public address of the host.
  * ``password`` the password of the host.
  * ``key`` the content of the keyfile used to login to the host.


.. cfy:node:: cloudify.hostpool.nodes.LinuxHost


.. cfy:node:: cloudify.hostpool.nodes.WindowsHost


Data Types
----------

.. cfy:datatype:: cloudify.datatypes.hostpool.Filters


Host-Pool Service
-----------------

The Host-Pool Service is a web service designed for managing a large pool of hosts to be used by cloudify deployments.
It allows for the use of multiple existing hosts to be allocated for a deployment. Supports defining hosts by:

  * os
  * name
  * endpoint (IP)
  * additional filters

The Host-Pool-Plugin will make calls to this service each time a new host
needs to be provisioned/terminated.

To make the installation of this service easy, we have made it available as a regular cloudify node type.

.. cfy:node:: cloudify.nodes.HostPoolService

**Attributes:**

  * ``seed_config`` the initial configuration of the host pool.
  * ``working_directory`` the final working directory of the service
  * ``endpoint`` the url of the service.
    This URL is determined by combining the ``port`` property of the type,
    with the ip of the host the service is contained within.

    The ip is either the ``ip`` attribute of the containing host node,
    or, in case it is absent, the ``ip`` property of the node.
    You can effectively think of this endpoint like the cloud endpoints
    you are probably used to.
  * ``service name`` defaults to cloudify-hostpool.

.. note::
    Complete definition of this type can be found
    `Here <https://github.com/cloudify-cosmo/cloudify-host-pool-service/blob/master/host-pool-service.yaml>`_.

    You must have a running Host-Pool Service before you can start using the Plugin
