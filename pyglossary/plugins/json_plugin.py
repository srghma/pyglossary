# -*- coding: utf-8 -*-

from pyglossary.plugins.formats_common import *

enable = True
lname = "json"
format = "Json"
description = "JSON (.json)"
extensions = (".json",)
extensionCreate = ".json"
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/JSON"
website = (
	"https://www.json.org/json-en.html",
	"www.json.org",
)
optionsProp = {
	"encoding": EncodingOption(),
	"enable_info": BoolOption(comment="Enable glossary info / metedata"),
	"resources": BoolOption(comment="Enable resources / data files"),
	"word_title": BoolOption(
		comment="add headwords title to beginning of definition",
	),
}


class Writer(object):
	_encoding: str = "utf-8"
	_enable_info: bool = True
	_resources: bool = True
	_word_title: bool = False

	compressions = stdCompressions

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = None
		glos.preventDuplicateWords()

	def open(self, filename: str):
		self._filename = filename

	def finish(self):
		self._filename = None

	def write(self) -> "Generator[None, BaseEntry, None]":
		from json import dumps
		from pyglossary.text_writer import writeTxt

		glos = self._glos
		encoding = self._encoding
		enable_info = self._enable_info
		resources = self._resources

		ascii = encoding == "ascii"

		def escape(st):
			return dumps(st, ensure_ascii=ascii)

		yield from writeTxt(
			glos,
			entryFmt="\t{word}: {defi},\n",
			filename=self._filename,
			encoding=encoding,
			writeInfo=enable_info,
			wordEscapeFunc=escape,
			defiEscapeFunc=escape,
			ext=".json",
			head="{\n",
			tail='\t"": ""\n}',
			resources=resources,
			word_title=self._word_title,
		)
