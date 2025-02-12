#encoding=utf-8

# Copyright (C) 2016 Intel Corporation
# Copyright (C) 2016 Broadcom
# Copyright (C) 2020 Collabora, Ltd.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice (including the next
# paragraph) shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import xml.parsers.expat
import sys
import operator
from functools import reduce

global_prefix = "mali"

pack_header = """
/* Generated code, see midgard.xml and gen_pack_header.py
 *
 * Packets, enums and structures for Panfrost.
 *
 * This file has been generated, do not hand edit.
 */

#ifndef PAN_PACK_H
#define PAN_PACK_H

#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <assert.h>
#include <math.h>
#include <inttypes.h>
#include "util/macros.h"
#include "util/u_math.h"

/* Assume that the caller has done adequate bounds checking */
//typedef uint64_t * pan_command_stream;
typedef struct pan_command_stream {
   union {
      uint32_t values[1];
      uint64_t *ptr;
   };
} pan_command_stream;

struct pan_command_stream_decoded {
  uint32_t values[256];
};

#define __gen_unpack_float(x, y, z) uif(__gen_unpack_uint(x, y, z))

static inline uint64_t
__gen_uint(uint64_t v, uint32_t start, uint32_t end)
{
#ifndef NDEBUG
   const int width = end - start + 1;
   if (width < 64) {
      const uint64_t max = (1ull << width) - 1;
      assert(v <= max);
   }
#endif

   return v << start;
}

static inline uint32_t
__gen_sint(int32_t v, uint32_t start, uint32_t end)
{
#ifndef NDEBUG
   const int width = end - start + 1;
   if (width < 64) {
      const int64_t max = (1ll << (width - 1)) - 1;
      const int64_t min = -(1ll << (width - 1));
      assert(min <= v && v <= max);
   }
#endif

   return (((uint32_t) v) << start) & ((2ll << end) - 1);
}

static inline uint32_t
__gen_padded(uint32_t v, uint32_t start, uint32_t end)
{
    unsigned shift = __builtin_ctz(v);
    unsigned odd = v >> (shift + 1);

#ifndef NDEBUG
    assert((v >> shift) & 1);
    assert(shift <= 31);
    assert(odd <= 7);
    assert((end - start + 1) == 8);
#endif

    return __gen_uint(shift | (odd << 5), start, end);
}


static inline uint64_t
__gen_unpack_uint(const uint8_t *restrict cl, uint32_t start, uint32_t end)
{
   uint64_t val = 0;
   const int width = end - start + 1;
   const uint64_t mask = (width == 64 ? ~0 : (1ull << width) - 1 );

   for (uint32_t byte = start / 8; byte <= end / 8; byte++) {
      val |= ((uint64_t) cl[byte]) << ((byte - start / 8) * 8);
   }

   return (val >> (start % 8)) & mask;
}

static inline uint64_t
__gen_unpack_sint(const uint8_t *restrict cl, uint32_t start, uint32_t end)
{
   int size = end - start + 1;
   int64_t val = __gen_unpack_uint(cl, start, end);

   /* Get the sign bit extended. */
   return (val << (64 - size)) >> (64 - size);
}

static inline uint64_t
__gen_unpack_padded(const uint8_t *restrict cl, uint32_t start, uint32_t end)
{
   unsigned val = __gen_unpack_uint(cl, start, end);
   unsigned shift = val & 0b11111;
   unsigned odd = val >> 5;

   return (2*odd + 1) << shift;
}

static inline void
__gen_clear_value(uint8_t *restrict cl, uint32_t start, uint32_t end)
{
   for (uint32_t byte = start / 8; byte <= end / 8; byte++) {
      uint8_t m = 0;
      if (byte == start / 8)
         m |= 0xff >> (8 - start % 8);
      if (byte == end / 8)
         m |= 0xff << (1 + end % 8);

      cl[byte] &= m;
   }
}

#define PREFIX1(A) MALI_ ## A
#define PREFIX2(A, B) MALI_ ## A ## _ ## B
#define PREFIX4(A, B, C, D) MALI_ ## A ## _ ## B ## _ ## C ## _ ## D

#define pan_prepare(dst, T)                                 \\
   *(dst) = (struct PREFIX1(T)){ PREFIX2(T, header) }

#define pan_pack(dst, T, name)                              \\
   for (struct PREFIX1(T) name = { PREFIX2(T, header) }, \\
        *_loop_terminate = (void *) (dst);                  \\
        __builtin_expect(_loop_terminate != NULL, 1);       \\
        ({ PREFIX2(T, pack)((uint32_t *) (dst), &name);  \\
           _loop_terminate = NULL; }))

#define pan_unpack(src, T, name)                        \\
        struct PREFIX1(T) name;                         \\
        PREFIX2(T, unpack)((uint8_t *)(src), &name)

#define pan_print(fp, T, var, indent)                   \\
        PREFIX2(T, print)(fp, &(var), indent)

#define pan_size(T) PREFIX2(T, LENGTH)
#define pan_alignment(T) PREFIX2(T, ALIGN)

#define pan_section_offset(A, S) \\
        PREFIX4(A, SECTION, S, OFFSET)

#define pan_section_ptr(base, A, S) \\
        ((void *)((uint8_t *)(base) + pan_section_offset(A, S)))

#define pan_section_pack(dst, A, S, name)                                                         \\
   for (PREFIX4(A, SECTION, S, TYPE) name = { PREFIX4(A, SECTION, S, header) }, \\
        *_loop_terminate = (void *) (dst);                                                        \\
        __builtin_expect(_loop_terminate != NULL, 1);                                             \\
        ({ PREFIX4(A, SECTION, S, pack) (pan_section_ptr(dst, A, S), &name);              \\
           _loop_terminate = NULL; }))

#define pan_section_unpack(src, A, S, name)                               \\
        PREFIX4(A, SECTION, S, TYPE) name;                             \\
        PREFIX4(A, SECTION, S, unpack)(pan_section_ptr(src, A, S), &name)

#define pan_section_print(fp, A, S, var, indent)                          \\
        PREFIX4(A, SECTION, S, print)(fp, &(var), indent)

static inline void pan_merge_helper(uint32_t *dst, const uint32_t *src, size_t bytes)
{
        assert((bytes & 3) == 0);

        for (unsigned i = 0; i < (bytes / 4); ++i)
                dst[i] |= src[i];
}

#define pan_merge(packed1, packed2, type) \
        pan_merge_helper((packed1).opaque, (packed2).opaque, pan_size(type))

/* From presentations, 16x16 tiles externally. Use shift for fast computation
 * of tile numbers. */

#define MALI_TILE_SHIFT 4
#define MALI_TILE_LENGTH (1 << MALI_TILE_SHIFT)

"""

v6_format_printer = """

#define mali_pixel_format_print(fp, format) \\
    fprintf(fp, "%*sFormat (v6): %s%s%s %s%s%s%s\\n", indent, "", \\
        mali_format_as_str((enum mali_format)((format >> 12) & 0xFF)), \\
        (format & (1 << 20)) ? " sRGB" : "", \\
        (format & (1 << 21)) ? " big-endian" : "", \\
        mali_channel_as_str((enum mali_channel)((format >> 0) & 0x7)), \\
        mali_channel_as_str((enum mali_channel)((format >> 3) & 0x7)), \\
        mali_channel_as_str((enum mali_channel)((format >> 6) & 0x7)), \\
        mali_channel_as_str((enum mali_channel)((format >> 9) & 0x7)));

"""

v7_format_printer = """

#define mali_pixel_format_print(fp, format) \\
    fprintf(fp, "%*sFormat (v7): %s%s %s%s\\n", indent, "", \\
        mali_format_as_str((enum mali_format)((format >> 12) & 0xFF)), \\
        (format & (1 << 20)) ? " sRGB" : "", \\
        mali_rgb_component_order_as_str((enum mali_rgb_component_order)(format & ((1 << 12) - 1))), \\
        (format & (1 << 21)) ? " XXX BAD BIT" : "");

"""

no_cs = "".join([f"""
#define MALI_{y} MALI_{x}
#define MALI_{y}_header MALI_{x}_header
#define MALI_{y}_pack MALI_{x}_pack
#define MALI_{y}_LENGTH MALI_{x}_LENGTH
#define MALI_{y}_ALIGN MALI_{x}_ALIGN
#define mali_{y.lower()}_packed mali_{x.lower()}_packed
#define MALI_{y}_unpack MALI_{x}_unpack
#define MALI_{y}_print MALI_{x}_print
""" for x, y in (("DRAW", "DRAW_NO_CS"), )]) + """

#define pan_pack_cs_v10(dst, _, T, name) pan_pack(dst, T, name)

#define pan_section_pack_cs_v10(dst, _, A, S, name) pan_section_pack(dst, A, S, name)

#define pan_unpack_cs_v10(dst, _, __, T, name) pan_unpack(dst, T, name)

#define pan_section_unpack_cs_v10(src, _, __, A, S, name) pan_section_unpack(src, A, S, name)
"""

with_cs = """
#define pan_pack_cs(dst, T, name)                       \\
   for (struct PREFIX1(T) name = { PREFIX2(T, header) }, \\
        *_loop_terminate = (void *) (dst);                  \\
        __builtin_expect(_loop_terminate != NULL, 1);       \\
        ({ PREFIX2(T, pack_cs)(dst, &name);  \\
           _loop_terminate = NULL; }))

#define pan_section_pack_cs(dst, A, S, name)                                                         \\
   for (PREFIX4(A, SECTION, S, TYPE) name = { PREFIX4(A, SECTION, S, header) }, \\
        *_loop_terminate = (void *) (dst);                                                        \\
        __builtin_expect(_loop_terminate != NULL, 1);                                             \\
        ({ PREFIX4(A, SECTION, S, pack_cs) (dst, &name);              \\
           _loop_terminate = NULL; }))

#define pan_section_pack_cs_v10(_, dst, A, S, name) pan_section_pack_cs(dst, A, S, name)

// TODO: assert that the first argument is NULL
#define pan_pack_cs_v10(_, dst, T, name) pan_pack_cs(dst, T, name)

#define pan_pack_ins(dst, T, name)                       \\
   for (struct PREFIX1(T) name = { PREFIX2(T, header) }, \\
        *_loop_terminate = (void *) (dst);                  \\
        __builtin_expect(_loop_terminate != NULL, 1);       \\
        ({ PREFIX2(T, pack_ins)(dst, &name);  \\
           _loop_terminate = NULL; }))

#define pan_unpack_cs(buf, buf_unk, T, name) \\
        struct PREFIX1(T) name; \\
        PREFIX2(T, unpack)(buf, buf_unk, &name)

#define pan_unpack_cs_v10(_, buf, buf_unk, T, name) pan_unpack_cs(buf, buf_unk, T, name)

#define pan_section_unpack_cs_v10(_, buf, buf_unk, A, S, name) \\
        PREFIX4(A, SECTION, S, TYPE) name;                             \\
        PREFIX4(A, SECTION, S, unpack)(buf, buf_unk, &name)

static inline void
pan_emit_cs_ins(pan_command_stream *s, uint8_t op, uint64_t instr)
{
   assert(instr < (1ULL << 56));
   instr |= ((uint64_t)op << 56);
   *((s->ptr)++) = instr;
}

static inline void
pan_emit_cs_32(pan_command_stream *s, uint8_t index, uint32_t value)
{
   pan_emit_cs_ins(s, 2, ((uint64_t) index << 48) | value);
}

static inline void
pan_emit_cs_48(pan_command_stream *s, uint8_t index, uint64_t value)
{
   assert(value < (1ULL << 48));
   pan_emit_cs_ins(s, 1, ((uint64_t) index << 48) | value);
}
"""

def to_alphanum(name):
    substitutions = {
        ' ': '_',
        '/': '_',
        '[': '',
        ']': '',
        '(': '',
        ')': '',
        '-': '_',
        ':': '',
        '.': '',
        ',': '',
        '=': '',
        '>': '',
        '#': '',
        '&': '',
        '%': '',
        '*': '',
        '"': '',
        '+': '',
        '\'': '',
    }

    for i, j in substitutions.items():
        name = name.replace(i, j)

    return name

def safe_name(name):
    name = to_alphanum(name)
    if not name[0].isalpha():
        name = '_' + name

    return name

def prefixed_upper_name(prefix, name):
    if prefix:
        name = prefix + "_" + name
    return safe_name(name).upper()

def enum_name(name):
    return "{}_{}".format(global_prefix, safe_name(name)).lower()

def num_from_str(num_str):
    if num_str.lower().startswith('0x'):
        return int(num_str, base=16)
    else:
        assert(not num_str.startswith('0') and 'octals numbers not allowed')
        return int(num_str)

MODIFIERS = ["shr", "minus", "align", "log2"]

def parse_modifier(modifier):
    if modifier is None:
        return None

    for mod in MODIFIERS:
        if modifier[0:len(mod)] == mod:
            if mod == "log2":
                assert(len(mod) == len(modifier))
                return [mod]

            if modifier[len(mod)] == '(' and modifier[-1] == ')':
                ret = [mod, int(modifier[(len(mod) + 1):-1])]
                if ret[0] == 'align':
                    align = ret[1]
                    # Make sure the alignment is a power of 2
                    assert(align > 0 and not(align & (align - 1)));

                return ret

    print("Invalid modifier")
    assert(False)

class Aggregate(object):
    def __init__(self, parser, name, attrs):
        self.parser = parser
        self.sections = []
        self.name = name
        self.explicit_size = int(attrs["size"]) if "size" in attrs else 0
        self.size = 0
        self.align = int(attrs["align"]) if "align" in attrs else None

    class Section:
        def __init__(self, name):
            self.name = name

    def get_size(self):
        if self.size > 0:
            return self.size

        size = 0
        for section in self.sections:
            size = max(size, section.offset + section.type.get_length())

        if self.explicit_size > 0:
            assert(self.explicit_size >= size)
            self.size = self.explicit_size
        else:
            self.size = size
        return self.size

    def add_section(self, type_name, attrs):
        assert("name" in attrs)
        section = self.Section(safe_name(attrs["name"]).lower())
        section.human_name = attrs["name"]
        section.offset = int(attrs["offset"])
        assert(section.offset % 4 == 0)
        section.type = self.parser.structs[attrs["type"]]
        section.type_name = type_name
        self.sections.append(section)

class Field(object):
    def __init__(self, parser, attrs):
        self.parser = parser
        if "name" in attrs:
            self.name = safe_name(attrs["name"]).lower()
            self.human_name = attrs["name"]

        if ":" in str(attrs["start"]):
            (word, bit) = attrs["start"].split(":")
            self.start = (int(word, 0) * 32) + int(bit)
        else:
            self.start = int(attrs["start"])

        self.end = self.start + int(attrs["size"]) - 1
        self.type = attrs["type"]

        if self.type == 'bool' and self.start != self.end:
            print("#error Field {} has bool type but more than one bit of size".format(self.name));

        if "prefix" in attrs:
            self.prefix = safe_name(attrs["prefix"]).upper()
        else:
            self.prefix = None

        if "exact" in attrs:
            self.exact = int(attrs["exact"])
        else:
            self.exact = None

        self.default = attrs.get("default")

        # Map enum values
        if self.type in self.parser.enums and self.default is not None:
            self.default = safe_name('{}_{}_{}'.format(global_prefix, self.type, self.default)).upper()

        self.modifier  = parse_modifier(attrs.get("modifier"))

    def emit_template_struct(self, dim):
        if self.type == 'address':
            type = 'uint64_t'
        elif self.type == 'bool':
            type = 'bool'
        elif self.type == 'float':
            type = 'float'
        elif self.type in ['uint', 'hex'] and self.end - self.start > 32:
            type = 'uint64_t'
        elif self.type == 'int':
            type = 'int32_t'
            # TODO: Convert to tuple
        elif self.type in ['uint', 'hex', 'register', 'uint/float', 'padded', 'Pixel Format']:
            type = 'uint32_t'
        elif self.type in self.parser.structs:
            type = 'struct ' + self.parser.gen_prefix(safe_name(self.type.upper()))
        elif self.type in self.parser.enums:
            type = 'enum ' + enum_name(self.type)
        else:
            print("#error unhandled type: %s" % self.type)
            type = "uint32_t"

        print("   %-36s %s%s;" % (type, self.name, dim))

        for value in self.values:
            name = prefixed_upper_name(self.prefix, value.name)
            print("#define %-40s %d" % (name, value.value))

    def overlaps(self, field):
        return self != field and max(self.start, field.start) <= min(self.end, field.end)

class Group(object):
    def __init__(self, parser, parent, start, count, label):
        self.parser = parser
        self.parent = parent
        self.start = start
        self.count = count
        self.label = label
        self.size = 0
        self.length = 0
        self.fields = []

    def get_length(self):
        # Determine number of bytes in this group.
        calculated = max(field.end // 8 for field in self.fields) + 1 if len(self.fields) > 0 else 0
        if self.length > 0:
            assert(self.length >= calculated)
        else:
            self.length = calculated
        return self.length


    def emit_template_struct(self, dim):
        if self.count == 0:
            print("   /* variable length fields follow */")
        else:
            if self.count > 1:
                dim = "%s[%d]" % (dim, self.count)

            if len(self.fields) == 0:
                print("   int dummy;")

            for field in self.fields:
                if field.exact is not None:
                    continue

                field.emit_template_struct(dim)

    class Word:
        def __init__(self, size=32):
            self.size = size
            self.contributors = []

    class FieldRef:
        def __init__(self, field, path, start, end):
            self.field = field
            self.path = path
            self.start = start
            self.end = end

    def collect_fields(self, fields, offset, path, all_fields):
        for field in fields:
            field_path = '{}{}'.format(path, field.name)
            field_offset = offset + field.start

            if field.type in self.parser.structs:
                sub_struct = self.parser.structs[field.type]
                self.collect_fields(sub_struct.fields, field_offset, field_path + '.', all_fields)
                continue

            start = field_offset
            end = offset + field.end
            all_fields.append(self.FieldRef(field, field_path, start, end))

    def collect_words(self, fields, offset, path, words, ins=False):
        for field in fields:
            field_path = '{}{}'.format(path, field.name)
            start = offset + field.start

            if field.type in self.parser.structs:
                sub_fields = self.parser.structs[field.type].fields
                self.collect_words(sub_fields, start, field_path + '.', words)
                continue

            end = offset + field.end
            contributor = self.FieldRef(field, field_path, start, end)
            first_word = contributor.start // 32
            last_word = contributor.end // 32
            if ins:
                assert(last_word < 2)
                first_word = last_word = 0

            for b in range(first_word, last_word + 1):
                if not b in words:
                    words[b] = self.Word(size=64 if ins else 32)

                words[b].contributors.append(contributor)

        return

    def emit_pack_function(self, csf=False, ins=False):
        if csf:
            self.length = 256 * 4
        else:
            self.get_length()
            assert(not ins)

        words = {}
        self.collect_words(self.fields, 0, '', words, ins=ins)

        # Validate the modifier is lossless
        for field in self.fields:
            if field.modifier is None:
                continue

            assert(field.exact is None)

            if field.modifier[0] == "shr":
                shift = field.modifier[1]
                mask = hex((1 << shift) - 1)
                print("   assert((values->{} & {}) == 0);".format(field.name, mask))
            elif field.modifier[0] == "minus":
                print("   assert(values->{} >= {});".format(field.name, field.modifier[1]))
            elif field.modifier[0] == "log2":
                print("   assert(util_is_power_of_two_nonzero(values->{}));".format(field.name))

        if ins:
            index_list = (0, )
        elif csf:
            index_list = sorted(words)
        else:
            index_list = range(self.length // 4)

        for index in index_list:
            # Handle MBZ words
            if not index in words:
                if ins:
                    print("   pan_emit_cs_ins(s, 0x%02x, 0);" % self.op)
                elif not csf:
                    print("   cl[%2d] = 0;" % index)
                continue

            word = words[index]

            word_start = index * 32

            size = 32
            # Can we move all fields from the next index here?
            if csf and index % 2 == 0 and index + 1 in words:
                word_next = words[index + 1]
                end = max(c.end for c in word_next.contributors)
                if end - word_start < 48:
                    size = 48
                    word.contributors += [x for x in word_next.contributors if not x in word.contributors]
                    del words[index + 1]

            v = None
            if ins:
                prefix = "   pan_emit_cs_ins(s, 0x%02x," % self.op
            elif size == 48:
                prefix = "   pan_emit_cs_48(s, 0x%02x," % index
            elif csf:
                prefix = "   pan_emit_cs_32(s, 0x%02x," % index
            else:
                prefix = "   cl[%2d] = (" % index

            for contributor in word.contributors:
                field = contributor.field
                name = field.name
                start = contributor.start
                end = contributor.end
                contrib_word_start = (start // word.size) * word.size
                start -= contrib_word_start
                end -= contrib_word_start

                value = str(field.exact) if field.exact is not None else "values->{}".format(contributor.path)
                if field.modifier is not None:
                    if field.modifier[0] == "shr":
                        value = "{} >> {}".format(value, field.modifier[1])
                    elif field.modifier[0] == "minus":
                        value = "{} - {}".format(value, field.modifier[1])
                    elif field.modifier[0] == "align":
                        value = "ALIGN_POT({}, {})".format(value, field.modifier[1])
                    elif field.modifier[0] == "log2":
                        value = "util_logbase2({})".format(value)

                if field.type in ["uint", "hex", "uint/float", "address", "register", "Pixel Format"]:
                    s = "__gen_uint(%s, %d, %d)" % \
                        (value, start, end)
                elif field.type == "padded":
                    s = "__gen_padded(%s, %d, %d)" % \
                        (value, start, end)
                elif field.type in self.parser.enums:
                    s = "__gen_uint(%s, %d, %d)" % \
                        (value, start, end)
                elif field.type == "int":
                    s = "__gen_sint(%s, %d, %d)" % \
                        (value, start, end)
                elif field.type == "bool":
                    s = "__gen_uint(%s, %d, %d)" % \
                        (value, start, end)
                elif field.type == "float":
                    assert(start == 0 and end == 31)
                    s = "__gen_uint(fui({}), 0, 32)".format(value)
                else:
                    s = "#error unhandled field {}, type {}".format(contributor.path, field.type)

                if not s == None:
                    shift = word_start - contrib_word_start
                    if shift > 0:
                        s = "%s >> %d" % (s, shift)
                    elif shift < 0:
                        s = "%s << %d" % (s, -shift)

                    if contributor == word.contributors[-1]:
                        print("%s %s);" % (prefix, s))
                    else:
                        print("%s %s |" % (prefix, s))
                    prefix = "           "

            continue

    # Given a field (start, end) contained in word `index`, generate the 32-bit
    # mask of present bits relative to the word
    def mask_for_word(self, index, start, end):
        field_word_start = index * 32
        start -= field_word_start
        end -= field_word_start
        # Cap multiword at one word
        start = max(start, 0)
        end = min(end, 32 - 1)
        count = (end - start + 1)
        return (((1 << count) - 1) << start)

    def emit_unpack_function(self, csf=False):
        # First, verify there is no garbage in unused bits
        words = {}
        self.collect_words(self.fields, 0, '', words)

        if not csf:
            for index in range(self.length // 4):
                base = index * 32
                word = words.get(index, self.Word())
                masks = [self.mask_for_word(index, c.start, c.end) for c in word.contributors]
                mask = reduce(lambda x,y: x | y, masks, 0)

                ALL_ONES = 0xffffffff

                if mask != ALL_ONES:
                    TMPL = '   if (((const uint32_t *) cl)[{}] & {}) fprintf(stderr, "XXX: Invalid field of {} unpacked at word {}\\n");'
                    print(TMPL.format(index, hex(mask ^ ALL_ONES), self.label, index))

        fieldrefs = []
        self.collect_fields(self.fields, 0, '', fieldrefs)
        for fieldref in fieldrefs:
            field = fieldref.field
            convert = None

            args = []
            args.append('cl')
            args.append(str(fieldref.start))
            args.append(str(fieldref.end))

            if field.type in set(["uint", "hex", "uint/float", "address", "register", "Pixel Format"]):
                convert = "__gen_unpack_uint"
            elif field.type in self.parser.enums:
                convert = "(enum %s)__gen_unpack_uint" % enum_name(field.type)
            elif field.type == "int":
                convert = "__gen_unpack_sint"
            elif field.type == "padded":
                convert = "__gen_unpack_padded"
            elif field.type == "bool":
                convert = "__gen_unpack_uint"
            elif field.type == "float":
                convert = "__gen_unpack_float"
            else:
                s = "/* unhandled field %s, type %s */\n" % (field.name, field.type)

            suffix = ""
            prefix = ""
            if field.modifier:
                if field.modifier[0] == "minus":
                    suffix = " + {}".format(field.modifier[1])
                elif field.modifier[0] == "shr":
                    suffix = " << {}".format(field.modifier[1])
                if field.modifier[0] == "log2":
                    prefix = "1U << "

            decoded = '{}{}({}){}'.format(prefix, convert, ', '.join(args), suffix)

            print('   values->{} = {};'.format(fieldref.path, decoded))
            if field.modifier and field.modifier[0] == "align":
                mask = hex(field.modifier[1] - 1)
                print('   assert(!(values->{} & {}));'.format(fieldref.path, mask))

            if csf:
                print('   __gen_clear_value({});'.format(', '.join(['cl_unk'] + args[1:])))

    def emit_print_function(self):
        for field in self.fields:
            convert = None
            name, val = field.human_name, 'values->{}'.format(field.name)

            if field.type in self.parser.structs:
                pack_name = self.parser.gen_prefix(safe_name(field.type)).upper()
                print('   fprintf(fp, "%*s{}:\\n", indent, "");'.format(field.human_name))
                print("   {}_print(fp, &values->{}, indent + 2);".format(pack_name, field.name))
            elif field.type == "address":
                # TODO resolve to name
                print('   fprintf(fp, "%*s{}: 0x%" PRIx64 "\\n", indent, "", {});'.format(name, val))
            elif field.type in self.parser.enums:
                print('   fprintf(fp, "%*s{}: %s\\n", indent, "", {}_as_str({}));'.format(name, enum_name(field.type), val))
            elif field.type == "int":
                print('   fprintf(fp, "%*s{}: %d\\n", indent, "", {});'.format(name, val))
            elif field.type == "bool":
                print('   fprintf(fp, "%*s{}: %s\\n", indent, "", {} ? "true" : "false");'.format(name, val))
            elif field.type == "float":
                print('   fprintf(fp, "%*s{}: %f\\n", indent, "", {});'.format(name, val))
            elif field.type in ["uint", "hex"] and (field.end - field.start) >= 32:
                print('   fprintf(fp, "%*s{}: 0x%" PRIx64 "\\n", indent, "", {});'.format(name, val))
            elif field.type in ("hex", "register"):
                print('   fprintf(fp, "%*s{}: 0x%x\\n", indent, "", {});'.format(name, val))
            elif field.type == "uint/float":
                print('   fprintf(fp, "%*s{}: 0x%X (%f)\\n", indent, "", {}, uif({}));'.format(name, val, val))
            elif field.type == "Pixel Format":
                print('   mali_pixel_format_print(fp, {});'.format(val))
            else:
                print('   fprintf(fp, "%*s{}: %u\\n", indent, "", {});'.format(name, val))

class Value(object):
    def __init__(self, attrs):
        self.name = attrs["name"]
        self.value = int(attrs["value"], 0)

class Parser(object):
    def __init__(self):
        self.parser = xml.parsers.expat.ParserCreate()
        self.parser.StartElementHandler = self.start_element
        self.parser.EndElementHandler = self.end_element

        self.struct = None
        self.structs = {}
        # Set of enum names we've seen.
        self.enums = set()
        self.aggregate = None
        self.aggregates = {}

    def gen_prefix(self, name):
        return '{}_{}'.format(global_prefix.upper(), name)

    def start_element(self, name, attrs):
        if name == "panxml":
            print(pack_header)
            if "arch" in attrs:
                arch = int(attrs["arch"])
                if arch <= 6:
                    print(v6_format_printer)
                else:
                    print(v7_format_printer)
                if arch < 10:
                    print(no_cs)
                else:
                    print(with_cs)
        elif name == "struct":
            name = attrs["name"]
            self.layout = attrs.get("layout", "struct")
            object_name = self.gen_prefix(safe_name(name.upper()))
            self.struct = object_name

            self.group = Group(self, None, 0, 1, name)
            if "size" in attrs:
                self.group.length = int(attrs["size"]) * 4
            self.group.align = int(attrs["align"]) if "align" in attrs else None
            self.group.op = int(attrs["op"]) if "op" in attrs else None
            self.structs[attrs["name"]] = self.group
            self.unpacked_alias = self.gen_prefix(safe_name(attrs["unpacked"].upper())) if "unpacked" in attrs else None
        elif name == "field":
            self.values = []
            self.skip_field = self.layout == "cs" and not attrs["start"].startswith("0x")
            if self.skip_field:
                #print(f"#warning Skipping non-CS field {attrs['name']}")
                return
            self.group.fields.append(Field(self, attrs))
        elif name == "enum":
            self.values = []
            self.enum = safe_name(attrs["name"])
            self.enums.add(attrs["name"])
            if "prefix" in attrs:
                self.prefix = attrs["prefix"]
            else:
                self.prefix= None
        elif name == "value":
            self.values.append(Value(attrs))
        elif name == "aggregate":
            aggregate_name = self.gen_prefix(safe_name(attrs["name"].upper()))
            # TODO: Make .layout less "global"?
            self.layout = attrs.get("layout", "struct")
            self.aggregate = Aggregate(self, aggregate_name, attrs)
            self.aggregates[attrs['name']] = self.aggregate
        elif name == "section":
            type_name = self.gen_prefix(safe_name(attrs["type"].upper()))
            self.aggregate.add_section(type_name, attrs)

    def end_element(self, name):
        if name == "struct":
            self.emit_struct()
            self.struct = None
            self.group = None
        elif name  == "field":
            if not self.skip_field:
                self.group.fields[-1].values = self.values
        elif name  == "enum":
            self.emit_enum()
            self.enum = None
        elif name == "aggregate":
            self.emit_aggregate()
            self.aggregate = None
        elif name == "panxml":
            # Include at the end so it can depend on us but not the converse
            print('#include "panfrost-job.h"')
            print('#endif')

    def emit_header(self, name):
        default_fields = []
        for field in self.group.fields:
            if not type(field) is Field:
                continue
            if field.default is not None:
                default_fields.append("   .{} = {}".format(field.name, field.default))
            elif field.type in self.structs:
                default_fields.append("   .{} = {{ {}_header }}".format(field.name, self.gen_prefix(safe_name(field.type.upper()))))

        print('#define %-40s\\' % (name + '_header'))
        if default_fields:
            print(",  \\\n".join(default_fields))
        else:
            print('   0')
        print('')

    def emit_template_struct(self, name, group):
        if self.unpacked_alias:
            # TODO: Check the fields match
            print("#define %s %s" % (name, self.unpacked_alias))
        else:
            print("struct %s {" % name)
            group.emit_template_struct("")
            print("};\n")

    def emit_aggregate(self):
        aggregate = self.aggregate

        if self.layout == "struct":
            print("struct %s_packed {" % aggregate.name.lower())
            print("   uint32_t opaque[{}];".format(aggregate.get_size() // 4))
            print("};\n")
            print('#define {}_LENGTH {}'.format(aggregate.name.upper(), aggregate.size))
        else:
            assert(self.layout == "cs")

        if aggregate.align != None:
            print('#define {}_ALIGN {}'.format(aggregate.name.upper(), aggregate.align))
        for section in aggregate.sections:
            print('#define {}_SECTION_{}_TYPE struct {}'.format(aggregate.name.upper(), section.name.upper(), section.type_name))
            print('#define {}_SECTION_{}_header {}_header'.format(aggregate.name.upper(), section.name.upper(), section.type_name))
            print('#define {}_SECTION_{}_pack {}_pack'.format(aggregate.name.upper(), section.name.upper(), section.type_name))
            # TODO: Only when req'd
            print('#define {}_SECTION_{}_pack_cs {}_pack_cs'.format(aggregate.name.upper(), section.name.upper(), section.type_name))
            print('#define {}_SECTION_{}_unpack {}_unpack'.format(aggregate.name.upper(), section.name.upper(), section.type_name))
            print('#define {}_SECTION_{}_print {}_print'.format(aggregate.name.upper(), section.name.upper(), section.type_name))
            print('#define {}_SECTION_{}_OFFSET {}'.format(aggregate.name.upper(), section.name.upper(), section.offset))
        print("")

    def emit_pack_function(self, name, group):
        print("static inline void\n%s_pack(uint32_t * restrict cl,\n%sconst struct %s * restrict values)\n{" %
              (name, ' ' * (len(name) + 6), name))

        group.emit_pack_function()

        print("}\n\n")

        # Should be a whole number of words
        assert((group.length % 4) == 0)

        print('#define {} {}'.format (name + "_LENGTH", group.length))
        if group.align != None:
            print('#define {} {}'.format (name + "_ALIGN", group.align))
        print('struct {}_packed {{ uint32_t opaque[{}]; }};'.format(name.lower(), group.length // 4))

    def emit_cs_pack_function(self, name, group):
        print("static inline void\n%s_pack_cs(pan_command_stream * restrict s,\n%sconst struct %s * restrict values)\n{\n" %
              (name, ' ' * (len(name) + 6), name))

        group.emit_pack_function(csf=True)

        print("}\n\n")

        assert(group.length == 256 * 4)

    def emit_ins_pack_function(self, name, group):
        print("static inline void\n%s_pack_ins(pan_command_stream * restrict s,\n%sconst struct %s * restrict values)\n{" %
              (name, ' ' * (len(name) + 6), name))

        group.emit_pack_function(csf=True, ins=True)

        print("}\n\n")

        assert(group.length == 256 * 4)

    def emit_unpack_function(self, name, group):
        print("static inline void")
        print("%s_unpack(const uint8_t * restrict cl,\n%sstruct %s * restrict values)\n{" %
              (name.upper(), ' ' * (len(name) + 8), name))

        group.emit_unpack_function()

        print("}\n")

    def emit_cs_unpack_function(self, name, group):
        print("static inline void")
        print("%s_unpack(const uint32_t * restrict buffer, uint32_t * restrict buffer_unk,\n"
              "%sstruct %s * restrict values)\n{"
              "   const uint8_t *cl = (uint8_t *)buffer;\n"
              "   uint8_t *cl_unk = (uint8_t *)buffer_unk;\n" %
              (name.upper(), ' ' * (len(name) + 8), name))

        group.emit_unpack_function(csf=True)

        print("}\n")

    def emit_print_function(self, name, group):
        print("static inline void")
        print("{}_print(FILE *fp, const struct {} * values, unsigned indent)\n{{".format(name.upper(), name))

        group.emit_print_function()

        print("}\n")

    def emit_struct(self):
        name = self.struct

        self.emit_template_struct(self.struct, self.group)
        self.emit_header(name)
        if self.layout == "struct":
            self.emit_pack_function(self.struct, self.group)
            self.emit_unpack_function(self.struct, self.group)
        elif self.layout == "cs":
            self.emit_cs_pack_function(self.struct, self.group)
            self.emit_cs_unpack_function(self.struct, self.group)
        elif self.layout == "ins":
            # TODO: I don't think that the current unpack emit functions would
            # work
            self.emit_ins_pack_function(self.struct, self.group)
        else:
            assert(self.layout == "none")
        self.emit_print_function(self.struct, self.group)

    def emit_enum(self):
        e_name = enum_name(self.enum)
        prefix = e_name if self.enum != 'Format' else global_prefix
        print('enum {} {{'.format(e_name))

        for value in self.values:
            name = '{}_{}'.format(prefix, value.name)
            name = safe_name(name).upper()
            print('        % -36s = %6d,' % (name, value.value))
        print('};\n')

        print("static inline const char *")
        print("{}_as_str(enum {} imm)\n{{".format(e_name.lower(), e_name))
        print("    switch (imm) {")
        for value in self.values:
            name = '{}_{}'.format(prefix, value.name)
            name = safe_name(name).upper()
            print('    case {}: return "{}";'.format(name, value.name))
        print('    default: return "XXX: INVALID";')
        print("    }")
        print("}\n")

    def parse(self, filename):
        file = open(filename, "rb")
        self.parser.ParseFile(file)
        file.close()

if len(sys.argv) < 2:
    print("No input xml file specified")
    sys.exit(1)

input_file = sys.argv[1]

p = Parser()
p.parse(input_file)
