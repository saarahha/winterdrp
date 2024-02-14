"""
Module containing functions to generate astrometric/photometric calibration catalogs
for SEDMv2
"""

import logging
from astropy.table import Table

from mirar.catalog import BaseCatalog, Gaia2Mass
from mirar.catalog.vizier import PS1, SkyMapper
from mirar.catalog.vizier.sdss import SDSS, NotInSDSSError, in_sdss
from mirar.data.image_data import Image
from mirar.pipelines.sedmv2.config import (
    psfex_config_path,
    sextractor_photometry_config,
    swarp_config_path,
)
from mirar.processors.astromatic import PSFex, Sextractor, Swarp
from mirar.processors.astromatic.sextractor.sextractor import SEXTRACTOR_HEADER_KEY
from mirar.references import BaseReferenceGenerator, PS1Ref, SDSSRef

logger = logging.getLogger(__name__)

# generators -
def sedmv2_astrometric_catalog_generator(image: Image) -> Gaia2Mass:
    """
    Returns an astrometric catalog for sedmv2,
    either Gaia or 2MASS

    :param image: image to generate a catalog for
    :return: Gaia/2MASS catalog around image
    """
    temp_cat_path = image[SEXTRACTOR_HEADER_KEY]
    min_mag, max_mag = 10, 20
    cat = Gaia2Mass(
        min_mag=min_mag,
        max_mag=max_mag,
        search_radius_arcmin=5,  # 7.5,
        trim=True,
        image_catalog_path=temp_cat_path,
        filter_name="j",
    )
    return cat  # pylint: disable=duplicate-code


def sedmv2_photometric_catalog_generator(image: Image) -> BaseCatalog:
    """
    Generate a photometric calibration catalog for sedmv2 images

    For u band: SDSS if possible, otherwise Skymapper (otherwise fail)
    For g/r1: use PS1

    :param image: Image
    :return: catalog at image position
    """
    filter_name = image["FILTERID"]
    dec = image["DEC"]
    min_mag, max_mag = 10, 20

    if filter_name in ["u", "U"]:
        if in_sdss(image["RA"], image["DEC"]):
            return SDSS(
                min_mag=min_mag,
                max_mag=max_mag,
                search_radius_arcmin=5,
                filter_name=filter_name,
            )

        if dec < 0.0:
            return SkyMapper(
                min_mag=min_mag,
                max_mag=max_mag,
                search_radius_arcmin=5,
                filter_name=filter_name,
            )
        err = "U band image is in a field with no reference image."
        logger.error(err)
        raise NotInSDSSError(err)
    return PS1(min_mag=10, max_mag=20, search_radius_arcmin=5, filter_name=filter_name)


def sedmv2_reference_image_generator(image: Image) -> BaseReferenceGenerator:
    """
    Get a reference image generator for an sedmv2 image

    For u band: SDSS if possible, otherwise fail
    For g/r: use PS1

    :param image: image
    :return: Reference image generator
    """
    filter_name = image["FILTER"]
    logger.info(f"Filter is {filter_name}")

    if filter_name in ["u", "U"]:
        if in_sdss(image["RA"], image["DEC"]):
            logger.debug("Will query reference image from SDSS")
            return SDSSRef(filter_name=filter_name)

        err = "U band image is in a field with no reference image."
        logger.error(err)
        raise NotInSDSSError(err)

    logger.debug("Will query reference image from PS1")
    return PS1Ref(filter_name=filter_name)


# astromatic-related -
def sedmv2_reference_image_resampler(**kwargs) -> Swarp:
    """
    Generates a resampler for reference images

    :param kwargs: kwargs
    :return: Swarp processor
    """
    return Swarp(
        swarp_config_path=swarp_config_path, cache=True, subtract_bkg=True, **kwargs
    )


def sedmv2_reference_sextractor(output_sub_dir: str, gain: float) -> Sextractor:
    """
    Generates a sextractor processor for reference images

    :param output_sub_dir: output sui directory
    :param gain: gain of image
    :return: Sextractor processor
    """
    return Sextractor(
        gain=gain,
        output_sub_dir=output_sub_dir,
        cache=True,
        **sextractor_photometry_config,
    )


def sedmv2_reference_psfex(output_sub_dir: str, norm_fits: bool) -> PSFex:
    """
    Generates a PSFex processor for reference images

    :param output_sub_dir: output sui directory
    :param norm_fits: boolean
    :return: Sextractor processor
    """
    return PSFex(
        config_path=psfex_config_path,
        output_sub_dir=output_sub_dir,
        norm_fits=norm_fits,
    )

# purifiers -
def sedmv2_zogy_catalogs_purifier(sci_catalog, ref_catalog):
    """
    TODO: This should be in sedmv2?
    """
    good_sci_sources = (
        (sci_catalog["FLAGS"] == 0)
        & (sci_catalog["SNR_WIN"] > 5)
        & (sci_catalog["FWHM_WORLD"] < 4.0 / 3600)
        & (sci_catalog["FWHM_WORLD"] > 0.5 / 3600)
        & (sci_catalog["SNR_WIN"] < 1000)
    )

    good_ref_sources = (
        (ref_catalog["SNR_WIN"] > 5)
        & (ref_catalog["FWHM_WORLD"] < 5.0 / 3600)
        & (ref_catalog["FWHM_WORLD"] > 0.5 / 3600)
    )

    return good_sci_sources, good_ref_sources


def sedmv2_photcal_img_catalog_purifier(catalog: Table, image: Image) -> Table:
    """
    To hand to PhotCalibrator image_photometric_catalog_purifier; remove sources with 0 error
        reported in ref catalog, sources with large spread model, likely galaxies (kron),
        outliers (-99 value in PS1), {... #TODO: fill this in}
    Args:
        sci_catalog:
        ref_catalog:
        color_err_colnames:

    Returns: #TODO: fill this in
    """

    # things from default sextractor purifier
    # PREREQ: SWARP HAS BEEN RUN. so i can cut based on the resampled x and y

    # remove sources close to edge
    edge_width_pixels = 100
    x_lower_limit = edge_width_pixels
    x_upper_limit = image.get_data().shape[1] - edge_width_pixels
    y_lower_limit = edge_width_pixels
    y_upper_limit = image.get_data().shape[0] - edge_width_pixels

    # remove sources close to masked region
    # ...

    # FWHM
    # fwhm_threshold_arcsec = ...
    clean_mask = (
            (catalog["FLAGS"] == 0)  # TODO: find out what this is
            & (catalog["MAG_PSF"] != 99)  # remove sources with faulty PSF meas.
            #& (catalog["FWHM_WORLD"] < fwhm_threshold_arcsec / 3600.0)
            & (catalog["X_IMAGE"] > x_lower_limit)
            & (catalog["X_IMAGE"] < x_upper_limit)
            & (catalog["Y_IMAGE"] > y_lower_limit)
            & (catalog["Y_IMAGE"] < y_upper_limit)
    )

    # remove sources where PS1 reports 0 error (oops this is for ref
    # error_cols = [col for col in ps1.colnames if col.startswith('e_')]
    # diagnostic: the last error column is likely a magnitude error (not astrometry).
    # good_ref_sources = (
    # (ref_catalog["SNR_WIN"] > 5)
    # & (ref_catalog["FWHM_WORLD"] < 5.0 / 3600)
    # & (ref_catalog["FWHM_WORLD"] > 0.5 / 3600)
    #        (ref_catalog[error_cols[-1]].mask == False)
    # )
    print(f'purifying...\n original catalog length = '
          f'{len(catalog)}, \npure length = {len(catalog[clean_mask])}')

    return catalog[clean_mask]


# color corrections -
def sedmv2_color_function_ps1(
    image: Image,
) -> tuple[tuple[str, str], tuple[str, str], tuple[float, float]]:
    """
    Args:
        image: Image object undergoing photometric calibrations
    Returns:
        color_filts: the two PS1 columns that define color term
        color_errs: the two PS1 columns with associated errors
        firstguess_color_zp: first guess at color and zeropoint (constant for sedmv2)
    """

    img_filt = image["FILTER"]

    # filters which define the color term. e.g. if img_filt = g, color = g - r
    if img_filt.lower() in ["g", "r"]:
        color_filts = ["gmag", "rmag"]
    elif img_filt.lower() == "i":
        color_filts = ["rmag", "imag"]
    elif img_filt.lower() == "z":
        color_filts = ["imag", "zmag"]
    else:
        logger.debug(f"Unexpected image filter: {img_filt}, defaulted to color = g-r")
        color_filts = ["gmag", "rmag"]
    color_errs = ["e_" + color_filts[0], "e_" + color_filts[1]]

    firstguess_color_zp = [-0.4, 27]

    return color_filts, color_errs, firstguess_color_zp
