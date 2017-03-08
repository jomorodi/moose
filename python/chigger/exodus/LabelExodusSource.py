#pylint: disable=missing-docstring
#################################################################
#                   DO NOT MODIFY THIS HEADER                   #
#  MOOSE - Multiphysics Object Oriented Simulation Environment  #
#                                                               #
#            (c) 2010 Battelle Energy Alliance, LLC             #
#                      ALL RIGHTS RESERVED                      #
#                                                               #
#           Prepared by Battelle Energy Alliance, LLC           #
#             Under Contract No. DE-AC07-05ID14517              #
#              With the U. S. Department of Energy              #
#                                                               #
#              See COPYRIGHT for full restrictions              #
#################################################################
import vtk
from ExodusSource import ExodusSource
from ExodusReader import ExodusReader
import mooseutils
from .. import base
from .. import filters
from .. import utils

class LabelExodusSource(base.ChiggerSource2D):
    """
    Object for attaching labels to an ExodusSource object.

    Args:
        result[ExodusSource]: The ExodusSource object to label.
    """
    FILTER_TYPES = [filters.IdFilter, filters.CellCenters, filters.SelectVisiblePoints]

    @staticmethod
    def getOptions():
        opt = base.ChiggerSource2D().getOptions()
        opt += utils.FontOptions.get_options()
        opt.add('label_type', 'variable', "Specify the type of label to create.", vtype=str, allow=['point', 'cell', 'variable'])
        opt.setDefault('justification', 'center')
        opt.setDefault('vertical_justification', 'middle')
        return opt

    def __init__(self, exodus_source, **kwargs):
        super(LabelExodusSource, self).__init__(vtkmapper_type=vtk.vtkLabeledDataMapper, **kwargs)

        if not isinstance(exodus_source, ExodusSource):
            raise mooseutils.MooseException('The supplied object of type {} must be a ExodusSource object.'.format(exodus_source.__class__.__name__))

        self._exodus_source = exodus_source

    def getVTKSource(self):
        """
        Returns the vtkExtractBlock object used for pulling subdomsin/sideset/nodeset data from the reader. (override)

        Returns:
            vtk.vtkExtractBlock (see ChiggerFilterSourceBase)
        """
        return self._exodus_source.getFilters()[-1].getVTKFilter()

    def update(self, **kwargs):
        """
        Update the settings for this object.
        """

        # Update the ExodusSource object to be labeled
        if self._exodus_source.needsUpdate():
            self._exodus_source.update()

        # Apply options (update can't be called here b/c the required filters need to be set first)
        self._setInitialOptions()
        self.setOptions(**kwargs)

        # Update the required filters based on the label type.
        label_type = self.getOption('label_type')
        if label_type == 'cell':
            self._required_filters = [filters.IdFilter(), filters.CellCenters(), filters.SelectVisiblePoints()]
            self._vtkmapper.SetLabelModeToLabelIds()
        elif label_type == 'point':
            self._required_filters = [filters.IdFilter(), filters.SelectVisiblePoints()]
            self._vtkmapper.SetLabelModeToLabelIds()
        else:
            varinfo = self._exodus_source.getCurrentVariableInformation()
            if varinfo.object_type == ExodusReader.ELEMENTAL:
                self._required_filters = [filters.CellCenters(), filters.SelectVisiblePoints()]
            else:
                self._required_filters = [filters.SelectVisiblePoints()]
            self._vtkmapper.SetFieldDataName(self._exodus_source.getOption('variable'))
            self._vtkmapper.SetLabelModeToLabelFieldData()

        # Call base class to connect filters/mappers
        super(LabelExodusSource, self).update()

        # Set the renderer for the SelectVisiblePoints filter
        self._required_filters[-1].getVTKFilter().SetRenderer(self._vtkrenderer)

        # Update fonts
        utils.FontOptions.set_options(self._vtkmapper.GetLabelTextProperty(), self._options)
