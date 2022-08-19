import logging
from glob import glob
from astropy.io import fits
from winterdrp.references.base_reference_generator import BaseReferenceGenerator
import numpy as np
from astroquery.sdss import SDSS
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS
import astropy.units as u
from winterdrp.references import ReferenceImageError

logger = logging.getLogger(__name__)


class SDSSRef(BaseReferenceGenerator):
    abbreviation = "sdss_ref_lookup"

    def __init__(
            self,
            filter_name: str,
    ):
        super(SDSSRef, self).__init__(filter_name)

    def get_reference(
            self,
            header: fits.Header
    ) -> fits.PrimaryHDU:
        nx, ny = header['NAXIS1'], header['NAXIS2']

        w = WCS(header)
        ra_cent, dec_cent = w.all_pix2world(nx, ny, 0)
        logger.info(f'Querying SDSS image around {ra_cent},{dec_cent}')
        crd = SkyCoord(ra=ra_cent, dec=dec_cent, unit=(u.deg, u.deg))
        rad = 10
        imgs = []
        while rad<100:
            imgs = SDSS.get_images(crd, radius=rad * u.arcsec, band=self.filter_name.lower())
            if imgs is not None:
                break
            logger.info(f'No source found within {rad} arcsec, will try with a larger radius')
            rad += 10
        if len(imgs)==0:
            err = f'Reference image not found from SDSS'
            logger.error(err)
            raise ReferenceImageError(err)
        else:
            refHDU = imgs[0][0].copy()
            refHDU.header['GAIN'] = 1
            refHDU.header['ZP'] = 2.5*9 # Unit of the image is nanomaggie
            del refHDU.header['HISTORY']
        return refHDU