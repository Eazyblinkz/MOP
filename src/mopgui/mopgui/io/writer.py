__author__ = "David Rusk <drusk@uvic.ca>"


class MPCWriter(object):
    """
    Writes out data about accepted objects in the Minor Planet Center's
    format as specified here:
    http://www.minorplanetcenter.net/iau/info/OpticalObs.html

    Note that we assume objects fall under the Minor Planet category.

    Format reproduced below for convenience:

        Columns     Format   Use
        1 -  5        A5     Minor planet number
        6 - 12        A7     Provisional or temporary designation
        13            A1     Discovery asterisk
        14            A1     Note 1
        15            A1     Note 2
        16 - 32              Date of observation
        33 - 44              Observed RA (J2000.0)
        45 - 56              Observed Decl. (J2000.0)
        57 - 65       9X     Must be blank
        66 - 71    F5.2,A1   Observed magnitude and band
                               (or nuclear/total flag for comets)
        72 - 77       X      Must be blank
        78 - 80       A3     Observatory code
    """

    def __init__(self, filehandle):
        self.filehandle = filehandle

    def write_line(self,
                   minor_plant_number,
                   provisional_name,
                   discovery_asterisk,
                   note1,
                   note2,
                   date_of_ob,
                   ra,
                   dec,
                   obs_mag,
                   band,
                   observatory_code="568"):
        # TODO: handle inputs of different lengths (ex: proper padding)
        # TODO: handle inputs of different types (str vs int vs float)
        # TODO: check for invalid values
        self.filehandle.write(
            minor_plant_number + provisional_name + discovery_asterisk +
            note1 + note2 + date_of_ob + ra + dec + " " * 9 + obs_mag + band +
            " " * 6 + observatory_code + "\n")
        self.filehandle.flush()


class AcceptRejectResultsWriter(object):
    """
    A simplified output that just writes the source name and whether it
    was accepted or rejected.  It just does formatting, it must be provided
    with all required data.
    """

    def __init__(self, filehandle, name_generator):
        # XXX name generator not used
        self.name_generator = name_generator
        self.filehandle = filehandle

    def write_result(self, sourcename, status):
        self.filehandle.write("%s: %s\n" % (sourcename, status))

    def close(self):
        self.filehandle.close()

