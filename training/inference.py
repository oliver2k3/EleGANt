from typing import List
import numpy as np
import cv2
from PIL import Image
import torch
import torch.nn.functional as F
from torchvision.transforms import ToPILImage

from training.solver import Solver
from training.preprocess import PreProcess
from models.modules.pseudo_gt import expand_area, mask_blend

class InputSample:
    def __init__(self, inputs, apply_mask=None):
        self.inputs = inputs
        self.transfer_input = None
        self.attn_out_list = None
        self.apply_mask = apply_mask

    def clear(self):
        self.transfer_input = None
        self.attn_out_list = None


class Inference:
    """
    An inference wrapper for makeup transfer.
    It takes two image `source` and `reference` in,
    and transfers the makeup of reference to source.
    """
    def __init__(self, config, args, model_path="G.pth"):

        self.device = args.device
        self.solver = Solver(config, args, inference=model_path)
        self.preprocess = PreProcess(config, args.device)
        self.denoise = config.POSTPROCESS.WILL_DENOISE
        self.img_size = config.DATA.IMG_SIZE
        # TODO: can be a hyper-parameter
        self.eyeblur = {'margin': 12, 'blur_size':7}

    def prepare_input(self, *data_inputs):
        """
        data_inputs: List[image, mask, diff, lms]
        """
        inputs = []
        for i in range(len(data_inputs)):
            inputs.append(data_inputs[i].to(self.device).unsqueeze(0))
        # prepare mask
        inputs[1] = torch.cat((inputs[1][:,0:1], inputs[1][:,1:].sum(dim=1, keepdim=True)), dim=1)
        return inputs

    def postprocess(self, source, crop_face, result):
        if crop_face is not None:
            source = source.crop(
                (crop_face.left(), crop_face.top(), crop_face.right(), crop_face.bottom()))
        source = np.array(source)
        result = np.array(result)

        height, width = source.shape[:2]
        small_source = cv2.resize(source, (self.img_size, self.img_size))
        laplacian_diff = source.astype(
            np.float64) - cv2.resize(small_source, (width, height)).astype(np.float64)
        result = (cv2.resize(result, (width, height)) +
                  laplacian_diff).round().clip(0, 255)

        result = result.astype(np.uint8)

        if self.denoise:
            result = cv2.fastNlMeansDenoisingColored(result)
        result = Image.fromarray(result).convert('RGB')
        return result

    
    def generate_source_sample(self, source_input):
        """
        source_input: List[image, mask, diff, lms]
        """
        source_input = self.prepare_input(*source_input)
        return InputSample(source_input)

    def generate_reference_sample(self, reference_input, apply_mask=None, 
                                  source_mask=None, mask_area=None, saturation=1.0):
        """
        all the operations on the mask, e.g., partial mask, saturation, 
        should be finally defined in apply_mask
        """
        if source_mask is not None and mask_area is not None:
            apply_mask = self.generate_partial_mask(source_mask, mask_area, saturation)
            apply_mask = apply_mask.unsqueeze(0).to(self.device)
        reference_input = self.prepare_input(*reference_input)
        
        if apply_mask is None:
            apply_mask = torch.ones(1, 1, self.img_size, self.img_size).to(self.device)
        return InputSample(reference_input, apply_mask)


    def generate_partial_mask(self, source_mask, mask_area='full', saturation=1.0):
        """
        source_mask: (C, H, W), lip, face, left eye, right eye
        return: apply_mask: (1, H, W)
        """
        assert mask_area in ['full', 'skin', 'lip', 'eye']
        if mask_area == 'full':
            return torch.sum(source_mask[0:2], dim=0, keepdim=True) * saturation
        elif mask_area == 'lip':
            return source_mask[0:1] * saturation
        elif mask_area == 'skin':
            mask_l_eye = expand_area(source_mask[2:3], self.eyeblur['margin']) #* source_mask[1:2]
            mask_r_eye = expand_area(source_mask[3:4], self.eyeblur['margin']) #* source_mask[1:2]
            mask_eye = mask_l_eye + mask_r_eye
            #mask_eye = mask_blend(mask_eye, 1.0, source_mask[1:2], blur_size=self.eyeblur['blur_size'])
            mask_eye = mask_blend(mask_eye, 1.0, blur_size=self.eyeblur['blur_size'])
            return source_mask[1:2] * (1 - mask_eye) * saturation
        elif mask_area == 'eye':
            mask_l_eye = expand_area(source_mask[2:3], self.eyeblur['margin']) #* source_mask[1:2]
            mask_r_eye = expand_area(source_mask[3:4], self.eyeblur['margin']) #* source_mask[1:2]
            mask_eye = mask_l_eye + mask_r_eye
            #mask_eye = mask_blend(mask_eye, saturation, source_mask[1:2], blur_size=self.eyeblur['blur_size'])
            mask_eye = mask_blend(mask_eye, saturation, blur_size=self.eyeblur['blur_size'])
            return mask_eye
  

    @torch.no_grad()
    def interface_transfer(self, source_sample: InputSample, reference_samples: List[InputSample]):
        """
        Input: a source sample and multiple reference samples
        Return: PIL.Image, the fused result
        """
        # encode source
        if source_sample.transfer_input is None:
            source_sample.transfer_input = self.solver.G.get_transfer_input(*source_sample.inputs)
        
        # encode references
        for r_sample in reference_samples:
            if r_sample.transfer_input is None:
                r_sample.transfer_input = self.solver.G.get_transfer_input(*r_sample.inputs, True)

        # self attention
        if source_sample.attn_out_list is None:
            source_sample.attn_out_list = self.solver.G.get_transfer_output(
                    *source_sample.transfer_input, *source_sample.transfer_input
                )
        
        # full transfer for each reference
        for r_sample in reference_samples:
            if r_sample.attn_out_list is None:
                r_sample.attn_out_list = self.solver.G.get_transfer_output(
                    *source_sample.transfer_input, *r_sample.transfer_input
                )

        # fusion
        # if the apply_mask is changed without changing source and references,
        # only the following steps are required
        fused_attn_out_list = []
        for i in range(len(source_sample.attn_out_list)):
            init_attn_out = torch.zeros_like(source_sample.attn_out_list[i], device=self.device)
            fused_attn_out_list.append(init_attn_out)
        apply_mask_sum = torch.zeros((1, 1, self.img_size, self.img_size), device=self.device)
        
        for r_sample in reference_samples:
            if r_sample.apply_mask is not None:
                apply_mask_sum += r_sample.apply_mask
                for i in range(len(source_sample.attn_out_list)):
                    feature_size = r_sample.attn_out_list[i].shape[2]
                    apply_mask = F.interpolate(r_sample.apply_mask, feature_size, mode='nearest')
                    fused_attn_out_list[i] += apply_mask * r_sample.attn_out_list[i]

        # self as reference
        source_apply_mask = 1 - apply_mask_sum.clamp(0, 1)
        for i in range(len(source_sample.attn_out_list)):
            feature_size = source_sample.attn_out_list[i].shape[2]
            apply_mask = F.interpolate(source_apply_mask, feature_size, mode='nearest')
            fused_attn_out_list[i] += apply_mask * source_sample.attn_out_list[i]

        # decode
        result = self.solver.G.decode(
            source_sample.transfer_input[0], fused_attn_out_list
        )
        result = self.solver.de_norm(result).squeeze(0)
        result = ToPILImage()(result.cpu())
        return result

    
    def transfer(self, source: Image, reference: Image, postprocess=True, return_full_image=False):
        """
        Args:
            source (Image): The image where makeup will be transfered to.
            reference (Image): Image containing targeted makeup.
            postprocess (bool): Whether to apply postprocessing.
            return_full_image (bool): If True, returns tuple (face_result, full_image_result)
        Return:
            Image: Transfered image (face only or full image based on return_full_image).
        """
        # Store original image for full image output
        original_source = source.copy()
        
        source_input, face, crop_face = self.preprocess(source)
        reference_input, _, _ = self.preprocess(reference)
        if not (source_input and reference_input):
            return None if not return_full_image else (None, None)

        #source_sample = self.generate_source_sample(source_input)
        #reference_samples = [self.generate_reference_sample(reference_input)]
        #result = self.interface_transfer(source_sample, reference_samples)
        source_input = self.prepare_input(*source_input)
        reference_input = self.prepare_input(*reference_input)
        result = self.solver.test(*source_input, *reference_input)
        
        if not postprocess:
            face_result = result
        else:
            face_result = self.postprocess(source, crop_face, result)
        
        # If return_full_image is True, create full image with makeup applied to face region
        if return_full_image and crop_face is not None:
            full_result = self.paste_face_to_full_image(original_source, face_result, crop_face)
            return face_result, full_result
        elif return_full_image:
            # If no crop_face, return the face result as both outputs
            return face_result, face_result
        else:
            return face_result
    
    def transfer_with_intensity(self, source: Image, reference: Image, 
                              lip_intensity=1.0, skin_intensity=1.0, eye_intensity=1.0,
                              postprocess=True, return_full_image=False):
        """
        Transfer makeup với điều chỉnh độ đậm riêng cho từng vùng.
        
        Args:
            source (Image): The image where makeup will be transferred to.
            reference (Image): Image containing targeted makeup.
            lip_intensity (float): Intensity for lip makeup (0.0 - 1.5)
            skin_intensity (float): Intensity for skin makeup (0.0 - 1.5)
            eye_intensity (float): Intensity for eye makeup (0.0 - 1.5)
            postprocess (bool): Whether to apply postprocessing.
            return_full_image (bool): If True, returns tuple (face_result, full_image_result)
        
        Return:
            Image or tuple: Transferred image(s) with customized intensity per region.
        """
        original_source = source.copy()
        
        source_input, face, crop_face = self.preprocess(source)
        reference_input, _, _ = self.preprocess(reference)
        if not (source_input and reference_input):
            return None if not return_full_image else (None, None)

        source_mask = source_input[1]
        source_sample = self.generate_source_sample(source_input)
        
        # Tạo reference samples với độ đậm riêng cho từng vùng
        reference_samples = [
            self.generate_reference_sample(reference_input, source_mask=source_mask, 
                                         mask_area='lip', saturation=lip_intensity),
            self.generate_reference_sample(reference_input, source_mask=source_mask, 
                                         mask_area='skin', saturation=skin_intensity),
            self.generate_reference_sample(reference_input, source_mask=source_mask, 
                                         mask_area='eye', saturation=eye_intensity)
        ]
        
        result = self.interface_transfer(source_sample, reference_samples)
        
        if not postprocess:
            face_result = result
        else:
            face_result = self.postprocess(source, crop_face, result)
        
        if return_full_image and crop_face is not None:
            full_result = self.paste_face_to_full_image(original_source, face_result, crop_face)
            return face_result, full_result
        elif return_full_image:
            return face_result, face_result
        else:
            return face_result
    
    def paste_face_to_full_image(self, original_image: Image, face_result: Image, crop_face):
        """
        Paste the makeup-applied face back to the original full image with smooth blending.
        
        Args:
            original_image (Image): Original full image with background
            face_result (Image): Processed face image with makeup
            crop_face: dlib rectangle of the detected face region
        
        Return:
            Image: Full image with makeup applied to face region with smooth blending
        """
        import cv2
        
        # Convert to numpy arrays
        original_np = np.array(original_image)
        face_result_np = np.array(face_result)
        
        # Get crop coordinates
        left = max(0, crop_face.left())
        top = max(0, crop_face.top())
        right = min(original_np.shape[1], crop_face.right())
        bottom = min(original_np.shape[0], crop_face.bottom())
        
        # Resize face result to match the crop size
        crop_width = right - left
        crop_height = bottom - top
        face_resized = cv2.resize(face_result_np, (crop_width, crop_height), interpolation=cv2.INTER_LANCZOS4)
        
        # Create a smooth blending mask using ellipse
        mask = np.zeros((crop_height, crop_width), dtype=np.float32)
        
        # Create elliptical mask centered on the face
        center_x = crop_width // 2
        center_y = crop_height // 2
        axes_x = int(crop_width * 0.45)  # 90% of half width
        axes_y = int(crop_height * 0.5)   # 100% of half height
        
        cv2.ellipse(mask, (center_x, center_y), (axes_x, axes_y), 0, 0, 360, 1, -1)
        
        # Apply Gaussian blur to create smooth transition
        blur_amount = max(crop_width, crop_height) // 10
        if blur_amount % 2 == 0:
            blur_amount += 1  # Must be odd
        blur_amount = max(blur_amount, 21)  # Minimum blur for smooth transition
        
        mask = cv2.GaussianBlur(mask, (blur_amount, blur_amount), 0)
        
        # Expand mask to 3 channels
        mask_3ch = np.stack([mask] * 3, axis=2)
        
        # Get the region from original image
        original_region = original_np[top:bottom, left:right]
        
        # Blend the face result with original using the mask
        blended_region = (face_resized * mask_3ch + original_region * (1 - mask_3ch)).astype(np.uint8)
        
        # Create result image
        result_np = original_np.copy()
        result_np[top:bottom, left:right] = blended_region
        
        # Convert back to PIL Image
        return Image.fromarray(result_np)

    def joint_transfer(self, source: Image, reference_lip: Image, reference_skin: Image,
                       reference_eye: Image, postprocess=True):
        source_input, face, crop_face = self.preprocess(source)
        lip_input, _, _ = self.preprocess(reference_lip)
        skin_input, _, _ = self.preprocess(reference_skin)
        eye_input, _, _ = self.preprocess(reference_eye)
        if not (source_input and lip_input and skin_input and eye_input):
            return None

        source_mask = source_input[1]
        source_sample = self.generate_source_sample(source_input)
        reference_samples = [
            self.generate_reference_sample(lip_input, source_mask=source_mask, mask_area='lip'),
            self.generate_reference_sample(skin_input, source_mask=source_mask, mask_area='skin'),
            self.generate_reference_sample(eye_input, source_mask=source_mask, mask_area='eye')
        ]
        
        result = self.interface_transfer(source_sample, reference_samples)
        
        if not postprocess:
            return result
        else:
            return self.postprocess(source, crop_face, result)