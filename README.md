# Doldrums

*To flutter: to move in quick, irregular motions, to beat rapidly, to be agitated.*  
*Doldrums: a period of stagnation.*

Doldrums is a reverse engineering tool for Flutter apps targetting Android. Concretely, it is a parser and information extractor for the Flutter/Dart Android binary, conventionally named `libapp.so`, for all Dart version 2.10 releases. When run, it outputs a full dump of all classes present in the isolate snapshot.

The tool is currently in **early beta**, and missing some deserialization routines and class information. It is likely that it won't work out-of-the-box.

## Dependencies

Doldrums requires [pyelftools](https://github.com/eliben/pyelftools) to parse the ELF format. You can install it with
```
pip3 install pyelftools
```

## Usage

To use, simply run the following command, substituting `libapp.so` for the appropriate binary, and `output` for the desired output file.
```
python3 main.py libapp.so output
```

The expected output is a dump of all classes, in the following format:
```
class MyApp extends StatelessWidget {
    Widget build(DynamicType, DynamicType) {
        Code at absolute offset: 0xec85c
    }

    String myPrint(DynamicType, DynamicType) {
        Code at absolute offset: 0xeca80
    }
}
```

The absolute code offset indicates the offset into the `libapp.so` file where the native function may be found.

## Reading material

For a detailed write-up on the format, please check my [blog post](https://rloura.wordpress.com/2020/12/04/reversing-flutter-for-android-wip/).

## Related works

[darter](https://github.com/mildsunrise/darter) is a fully implemented and fully tested parser for Dart version 2.5 releases.