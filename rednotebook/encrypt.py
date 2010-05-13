# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------
# Copyright (c) 2009  Jendrik Seipp
# 
# RedNotebook is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# RedNotebook is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with RedNotebook; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
# -----------------------------------------------------------------------

try:
	from Crypto.Cipher import Blowfish
except ImportError, err:
	Blowfish = None
	
import base64

# the block size for the cipher object; must be 8 for AES
BLOCK_SIZE = 8


# ----------------------------------------------------------------------
#
# Private functions

# Public domain code from http://idsvandermolen.com/codefiles/crypto.py

def nr_pad_bytes(blocksize, size):
	'Return number of required pad bytes for block of size.'
	if not (0 < blocksize < 255):
		raise Error('blocksize must be between 0 and 255')
	return blocksize - (size % blocksize)

def append_padding(blocksize, s):
	'''Append rfc 1423 padding to string.
	
	RFC 1423 algorithm adds 1 up to blocksize padding bytes to string s. Each 
	padding byte contains the number of padding bytes.
	'''
	n = nr_pad_bytes(blocksize, len(s))
	return s + (chr(n) * n)

def remove_padding(blocksize, s):
	'Remove rfc 1423 padding from string.'
	n = ord(s[-1]) # last byte contains number of padding bytes
	if n > blocksize or n > len(s):
		raise Error('invalid padding')
	return s[:-n]
	
# ----------------------------------------------------------------------

def encrypt_blowfish(cipher, string):
	string = append_padding(BLOCK_SIZE, string)
	return base64.b64encode(cipher.encrypt(string))
	
def decrypt_blowfish(cipher, encoded_string):
	dec_string = cipher.decrypt(base64.b64decode(encoded_string))
	return remove_padding(BLOCK_SIZE, dec_string)
	
	
	
# ----------------------------------------------------------------------
#
# Public functions

def encrypt(text, password):
	cipher = Blowfish.new(password)
	return encrypt_blowfish(cipher, text)
	
def decrypt(enc_text, password):
	cipher = Blowfish.new(password)
	return decrypt_blowfish(cipher, enc_text)
	
	
# ----------------------------------------------------------------------
#
# Testing

if __name__ == '__main__':
	secret_text = 'secret text\nwith üni¢ödé'
	password = 'password'
	enc_string = encrypt(secret_text, password)
	print 'Encrypted string:', enc_string
	dec_string = decrypt(enc_string, password)
	print 'Decrypted string:', dec_string
	assert secret_text == dec_string

