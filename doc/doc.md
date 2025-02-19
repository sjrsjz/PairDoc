# PairDoc

使用c-like的lexer来解析文档，然后生成文档的结构树，最后生成文档。

用 `#` 表示格式开始，使用花括号包裹格式内容，格式内容中的内容会被解析。

例如

```markdown
#format{content}

#format(argument1, argument2){content}

例如

#h1{Hello, #b{world}!}
```

考虑到lexer的特殊性，使用 `#n` 表示换行，使用 `#t` 表示tab。使用 `#s` 表示空格。

默认认定token之间完全由空格分隔，如果需要在token中使用空格，需要使用 `#s` 代替。


比如

```pairdoc
A apple a day keeps
the doctor away.

实际上是单行的，如果需要换行，需要使用 #n，如

A apple a day keeps #n
the doctor away.
```

默认认为 `\` 是转义字符（用于转义 `#`），如果需要使用 `\`，需要使用 `\\` 代替。
