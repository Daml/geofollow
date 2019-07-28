# -*- coding: utf-8 -*-
def classFactory(iface):
    """Load GeoFollow class from file GeoFollow.

    :param iface: A QGIS interface instance.
    :type iface: QgisInterface
    """
    #
    from .geofollow import GeoFollow
    return GeoFollow(iface)
