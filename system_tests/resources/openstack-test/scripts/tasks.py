from fabric.api import put
from cloudify import ctx


def copy_key(key_path, save_file_to):
    put(key_path, save_file_to)
    ctx.logger.info(
        'copied key from manager {0} to target {1}'
        .format(key_path, save_file_to)
    )
    ctx.source.instance.runtime_properties['key_path'] = save_file_to
