from astropy.wcs import WCS

from winterdrp.paths import BASE_NAME_KEY
from winterdrp.processors.base_processor import (
    BaseDataframeProcessor,
    BaseImageProcessor,
)
from winterdrp.processors.photometry.utils import (
    aper_photometry,
    make_psf_shifted_array,
    psf_photometry,
)


class BasePhotometry:
    def __init__(self):
        pass

    def perform_photometry(self, image_cutout, unc_image_cutout):
        raise NotImplementedError


class PSFPhotometry(BasePhotometry):
    def __init__(self, psf_filename: str):
        super().__init__()
        self.psf_filename = psf_filename

    def perform_photometry(self, image_cutout, unc_image_cutout):
        psfmodels = make_psf_shifted_array(
            psf_filename=self.psf_filename, cutout_size_psf_phot=image_cutout.shape[0]
        )

        flux, fluxunc, minchi2, xshift, yshift = psf_photometry(
            image_cutout, unc_image_cutout, psfmodels
        )
        return flux, fluxunc, minchi2, xshift, yshift


class AperturePhotometry(BasePhotometry):
    def __init__(
        self,
        aper_diameters: float | list[float] = 10.0,
        bkg_in_diameters: float | list[float] = 25.0,
        bkg_out_diameters: float | list[float] = 40.0,
    ):
        if not isinstance(aper_diameters, list):
            aper_diameters = [aper_diameters]
        if not isinstance(bkg_in_diameters, list):
            bkg_in_diameters = [bkg_in_diameters]
        if not isinstance(bkg_out_diameters, list):
            bkg_out_diameters = [bkg_out_diameters]
        super().__init__()

        self.aper_diameters = aper_diameters
        self.bkg_in_diameters = bkg_in_diameters
        self.bkg_out_diameters = bkg_out_diameters

    def perform_photometry(self, image_cutout, unc_image_cutout):
        fluxes, fluxuncs = [], []
        for ind, aper_diam in enumerate(self.aper_diameters):
            flux, fluxunc = aper_photometry(
                image_cutout,
                unc_image_cutout,
                self.aper_diameters[ind],
                self.bkg_in_diameters[ind],
                self.bkg_out_diameters[ind],
            )
            fluxes.append(flux)
            fluxuncs.append(fluxunc)
        return fluxes, fluxuncs


class BaseImagePhotometry(BaseImageProcessor):
    def __init__(
        self,
        phot_cutout_size: int = 20,
        target_ra_key: str = "TARGRA",
        target_dec_key: str = "TARGDEC",
    ):
        super().__init__()
        self.phot_cutout_size = phot_cutout_size
        self.target_ra_key = target_ra_key
        self.target_dec_key = target_dec_key

    def get_filenames(self, image):
        imagename = image.header[BASE_NAME_KEY]
        unc_filename = None
        return imagename, unc_filename

    def get_physical_coordinates(self, image):
        ra, dec = image[self.target_ra_key], image[self.target_dec_key]
        wcs = WCS(image.header)
        x, y = wcs.all_world2pix(ra, dec, 1)
        return x, y


class BaseCandidatePhotometry(BasePhotometry, BaseDataframeProcessor):
    def __init__(
        self,
        phot_cutout_size: int = 20,
        image_colname="diffimname",
        unc_image_colname="diffuncname",
        psf_file_colname="diffpsfname",
        x_colname="xpeak",
        y_colname="ypeak",
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.phot_cutout_size = phot_cutout_size
        self.image_colname = image_colname
        self.unc_image_colname = unc_image_colname
        self.psf_file_colname = psf_file_colname
        self.x_colname = x_colname
        self.y_colname = y_colname

    def get_filenames(self, row):
        imagename = row[self.image_colname]
        unc_filename = row[self.unc_image_colname]
        return imagename, unc_filename

    def get_physical_coordinates(self, row):
        x, y = row[self.x_colname], row[self.y_colname]
        return x, y
