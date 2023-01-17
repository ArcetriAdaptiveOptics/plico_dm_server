import unittest
import numpy as np
from PIL import Image
from plico_dm_server.controller.meadowlark_slm_1920 import \
    MeadowlarkSlm1920, MeadowlarkError
from plico_dm_server.controller.fake_meadowlark_slm_1920 import \
    FakeInitializeMeadowlarkSDK
from tempfile import gettempdir
import os


class MeadowlarkSlm1920Test(unittest.TestCase):

    WFC_FNAME = "pippo.bmp"
    WAVELEGTH_CALIBRATION = 635e-9  # meters
    MEAN_TEMPERATURE = 25.2  # celsius
    NUMBER_OF_ACTUATORS = 2211840
    HEIGHT = 1152
    WIDTH = 1920

    def setUp(self):
        self._sdk = FakeInitializeMeadowlarkSDK()
        self._slm_lib, self._image_lib = self._sdk.initialize_meadowlark_SDK()
        self.assertTrue(self._slm_lib.SDK_CONSTRUCTED)
        self._wfc_file_name = self._create_tmp_bmp()
        lut_file_name = 'pippo.lut'

        self._dm = MeadowlarkSlm1920(
            self._slm_lib, self._image_lib, lut_file_name,
            self._wfc_file_name, self.WAVELEGTH_CALIBRATION)

    def _create_tmp_bmp(self):
        # creating a temporary bmp image in the temporary directory
        my_temp_dir = gettempdir()
        im_wfc = Image.fromarray(
            np.zeros((self.HEIGHT, self.WIDTH), dtype=np.uint8))
        wfc_file_name = os.path.join(my_temp_dir, self.WFC_FNAME)
        im_wfc.save(wfc_file_name)
        return wfc_file_name

    def tearDown(self):
        os.remove(self._wfc_file_name)
        self.assertTrue(self._slm_lib.SDK_CONSTRUCTED)
        self._dm.deinitialize()

    @unittest.skip('Debug test')
    def testExceptionWhenSdkIsInizializedTwice(self):
        self._sdk.SDK_CONSTRUCTED_BEFORE = True
        self.assertRaises(Exception, self._sdk.initialize_meadowlark_SDK)

    @unittest.skip('Debug test')
    def testDeleteSdkWhenItsNotCreatedRaisesException(self):
        self._slm_lib.SDK_CONSTRUCTED = False
        self.assertRaises(
            Exception, self._slm_lib.Delete_SDK)
        # just to allow the tearDown
        self._slm_lib.SDK_CONSTRUCTED = True

    @unittest.skip('Debug test')
    def testGetNumberOfActuators(self):
        Nact = self._slm_lib.HEIGHT * self._slm_lib.WIDTH
        self.assertEqual(
            Nact,
            self._dm.getNumberOfActuators())

    @unittest.skip('Debug test')
    def testGetHeightAndWidthInPixels(self):
        width = self._slm_lib.WIDTH
        height = self._slm_lib.HEIGHT
        self.assertEqual(
            width, self._dm.getWidthInPixels())
        self.assertEqual(
            height, self._dm.getHeightInPixels())

    @unittest.skip('Debug test')
    def testSerialNumber(self):
        serial_number = self._slm_lib.VALID_SERIAL_NUMBER
        self.assertEqual(
            serial_number, self._dm.serialNumber())

    @unittest.skip('Debug test')
    def testGetTemperatureInCelsius(self):
        self.assertEqual(self.MEAN_TEMPERATURE,
                         self._dm.getTemperatureInCelsius())

    @unittest.skip('Debug test')
    def testModulo256Conversion(self):
        input_data = np.array([0, 0.2, 0.7,
                               1, 1.2, 1.9,
                               254, 254.2, 254.9,
                               255, 255.3, 256, 257, 258])
        expected_data = np.array([0, 0, 1,
                                  1, 1, 2,
                                  254, 254, 255,
                                  255, 255, 0, 1, 2], dtype=np.uint8)
        output_data = self._dm._convert2_modulo256(array=input_data, norm=255)

        self.assertEqual(expected_data.tolist(), output_data.tolist())

    @unittest.skip('Debug test')
    def testModulo256ConvertionOfTheSameArrayButWithDifferentShapes(self):
        one_dimensional_arr1 = np.array(np.arange(10), order='C')
        two_dimensional_arr2 = np.reshape(
            one_dimensional_arr1, (2, 5), order='C')
        # No normalization effects
        output_arr1 = self._dm._convert2_modulo256(
            array=one_dimensional_arr1, norm=255)
        output_arr2 = self._dm._convert2_modulo256(
            array=two_dimensional_arr2, norm=255)
        output_arr2 = np.reshape(output_arr2, (10), order='C')
        self.assertTrue(np.allclose(output_arr1, output_arr2))
        # Normalized
        output_arr1 = self._dm._convert2_modulo256(
            array=one_dimensional_arr1, norm=None)
        output_arr2 = self._dm._convert2_modulo256(
            array=two_dimensional_arr2, norm=None)
        output_arr2 = np.reshape(output_arr2, (10), order='C')
        self.assertTrue(np.allclose(output_arr1, output_arr2))

    @unittest.skip('Debug test')
    def testWriteImageWithWrongFloatInputArray(self):
        input_image = np.linspace(-1., 1.5, 10)
        self.assertRaises(
            MeadowlarkError, self._dm._write_image, input_image)

    @unittest.skip('Debug test')
    def testWriteImageError(self):
        self._slm_lib.FAIL_TASK_WRITE_IMAGE = True
        image = np.zeros(2, dtype=np.uint8, order='C')
        self.assertRaises(
            MeadowlarkError, self._dm._write_image, image_np=image)

    @unittest.skip('Debug test')
    def testImageWriteCompleteError(self):
        self._slm_lib.FAIL_TASK_WRITE_IMAGE_COMPLETE = True
        image = np.zeros(2, dtype=np.uint8, order='C')
        self.assertRaises(
            MeadowlarkError, self._dm._write_image, image_np=image)

    @unittest.skip('Debug test')
    def testWriteImageFromSameWfButWithDifferentDimension(self):
        # starting from the same wavefront
        Nact = self._slm_lib.HEIGHT * self._slm_lib.WIDTH
        one_dimensional_wf1 = np.array(np.arange(Nact), order='C')
        two_dimansional_wf2 = np.reshape(one_dimensional_wf1,
                                         (self._slm_lib.HEIGHT,
                                          self._slm_lib.WIDTH),
                                         order='C')
        # without wfc
        output_image1 = self._dm._write_image_from_wavefront(
            wavefront=one_dimensional_wf1, add_correction=False)
        output_image2 = self._dm._write_image_from_wavefront(
            wavefront=two_dimansional_wf2, add_correction=False)
        output_image2 = np.reshape(output_image2, (Nact,), order='C')
        self.assertTrue(np.allclose(output_image1, output_image2))
        # with wfc
        output_image1 = self._dm._write_image_from_wavefront(
            wavefront=one_dimensional_wf1, add_correction=True)
        output_image2 = self._dm._write_image_from_wavefront(
            wavefront=two_dimansional_wf2, add_correction=True)
        output_image2 = np.reshape(output_image2, (Nact,), order='C')
        self.assertTrue(np.allclose(output_image1, output_image2))

    @unittest.skip('Debug test')
    def testSetZonalCommandWithWrongSizeRaises(self):
        wrongNumberOfActuators = self.NUMBER_OF_ACTUATORS - 10
        # 1D input zonalCommand array
        commandVector1D = np.zeros(wrongNumberOfActuators)
        self.assertRaises(
            MeadowlarkError,
            self._dm.setZonalCommand,
            zonalCommand=commandVector1D)
        # 2D input zonalCommand array with both shapes wrong
        commandVectorWithWrongShapes = np.zeros((2, 2))
        self.assertRaises(
            MeadowlarkError,
            self._dm.setZonalCommand,
            zonalCommand=commandVectorWithWrongShapes)
        # 2D input zonalCommand array with wrong number of rows
        commandVectorWithWrongRows = np.zeros((self.HEIGHT, 2))
        self.assertRaises(
            MeadowlarkError,
            self._dm.setZonalCommand,
            zonalCommand=commandVectorWithWrongRows)
        # 2D input zonalCommand array with wrong number of columns
        commandVectorWithWrongCols = np.zeros((2, self.WIDTH))
        self.assertRaises(
            MeadowlarkError,
            self._dm.setZonalCommand,
            zonalCommand=commandVectorWithWrongCols)

    @unittest.skip('Debug test')
    def testSetAndGetZonalCommand(self):
        zonalCommand = np.arange(self.NUMBER_OF_ACTUATORS)
        self._dm.setZonalCommand(zonalCommand, add_correction=True)
        actualCommand = self._dm.getZonalCommand()
        self.assertTrue(np.allclose(zonalCommand, actualCommand))

    @unittest.skip('Debug test')
    def testNeed2CallWriteImageCompleteVariable(self):
        # testing NEED2CALL_WRITEIMAGECOMPLETE bool variable from FakeSlmLib
        # calling FakeSlmLib.Write_image and FakeSlmLib.ImageWriteComplete
        self.assertFalse(self._slm_lib.NEED2CALL_WRITEIMAGECOMPLETE)
        useless_input_parameters = np.zeros(8)

        # writing a single image
        self._slm_lib.Write_image(*useless_input_parameters)
        self.assertTrue(self._slm_lib.NEED2CALL_WRITEIMAGECOMPLETE)

        self._slm_lib.ImageWriteComplete(*useless_input_parameters[:2])
        self.assertFalse(self._slm_lib.NEED2CALL_WRITEIMAGECOMPLETE)

        # writing 2 image without checking if the buffer is ready
        # for the next image
        self._slm_lib.Write_image(*useless_input_parameters)
        self.assertRaises(
            Exception, self._slm_lib.Write_image, *useless_input_parameters)

        # writing and checking properly multiple images in sequence
        self._slm_lib.NEED2CALL_WRITEIMAGECOMPLETE = False
        for _ in np.arange(5):
            self._slm_lib.Write_image(*useless_input_parameters)
            self.assertTrue(self._slm_lib.NEED2CALL_WRITEIMAGECOMPLETE)
            self._slm_lib.ImageWriteComplete(*useless_input_parameters[:2])
            self.assertFalse(self._slm_lib.NEED2CALL_WRITEIMAGECOMPLETE)

    @unittest.skip('Debug test')
    def testImageWriteAndImageWriteCompleteCorrectSequence(self):
        self.assertFalse(self._slm_lib.NEED2CALL_WRITEIMAGECOMPLETE)
        image2write_on_slm = np.zeros(self.NUMBER_OF_ACTUATORS, dtype=np.uint8)
        # writing a single image on slm
        # calling _write_image
        self._dm._write_image(
            image_np=image2write_on_slm)
        self.assertFalse(self._slm_lib.NEED2CALL_WRITEIMAGECOMPLETE)
        # calling _ write_image_from_wavefront
        self._dm._write_image_from_wavefront(
            wavefront=image2write_on_slm,
            add_correction=False)
        self.assertFalse(self._slm_lib.NEED2CALL_WRITEIMAGECOMPLETE)
        # calling setZonalCommand
        self._dm.setZonalCommand(
            zonalCommand=image2write_on_slm,
            add_correction=False)
        self.assertFalse(self._slm_lib.NEED2CALL_WRITEIMAGECOMPLETE)
        # calling setZonalCommand in sequence
        for _ in np.arange(8):
            self._dm.setZonalCommand(
                zonalCommand=image2write_on_slm,
                add_correction=False)
            self.assertFalse(self._slm_lib.NEED2CALL_WRITEIMAGECOMPLETE)

    @unittest.skip('Debug test')
    def testImageWriteIsNotReady4TheNextImage(self):
        self.assertFalse(self._slm_lib.NEED2CALL_WRITEIMAGECOMPLETE)
        self._slm_lib.NEED2CALL_WRITEIMAGECOMPLETE = True
        image2write_on_slm = np.zeros(self.NUMBER_OF_ACTUATORS)
        self.assertRaises(
            Exception, self._dm.setZonalCommand, image2write_on_slm, False)

    @unittest.skip('Debug test')
    def testWriteImageWithWavefrontCorrection(self):
        wavefrontCorrection = np.ones(self.NUMBER_OF_ACTUATORS, dtype=np.uint8)
        image2WriteOnSlm = np.zeros(self.NUMBER_OF_ACTUATORS, dtype=np.uint8)
        self._dm._wfc = wavefrontCorrection
        outputImage = self._dm._write_image_from_wavefront(
            wavefront=image2WriteOnSlm,
            add_correction=True)
        expectedImage = image2WriteOnSlm + wavefrontCorrection
        self.assertTrue(np.allclose(expectedImage, outputImage))


if __name__ == "__main__":
    unittest.main()
