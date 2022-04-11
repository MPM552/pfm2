#!/usr/bin/perl -T
# The -T flag forces checking of tainted values, for security.

# CGI-bin script to call PFM program for Garifuna
# Raphael Finkel 2012

use CGI qw/:standard -debug/;
use Encode;
use strict;
use utf8;
# use_named_parameters(1);

# constants
	my $pfmDir = '.'; # '/homes/raphael/projects/pfm';
	my $parseProgram = "../pfm.cgi";

# globals
my (
	$root, $prefixedRoot, $hasObject, $gloss,
	@tenses, @polarities, @transitivities,
	@s_persons, @s_numbers, @s_genders,
	@o_persons, @o_numbers, @o_genders,
);

# global variables
	my ($Debug);

sub Untaint {
	my ($what) = @_;
	$what =~ s/[&*()`\$;|]//g; # remove suspicious characters
	$what =~ /(.*)/; # untaint
	return($1);
} # Untaint

sub forceValue {
	my ($param, $default) = @_;
	my $result = Untaint(decode_utf8(scalar param($param)));
	$result =~ s/\s//g;
	if (length($result) == 0) {
		$result = $default;
	}
	return $result;
}

sub init {
	$ENV{'PATH'} = '/bin:/usr/bin:/usr/local/bin:/usr/local/gnu/bin';
		# for security
	binmode STDIN, ":utf8";
	binmode STDOUT, ":utf8";
	$| = 1; # flush output
	for my $value (multi_param('tense')) {
		push @tenses, Untaint($value);
	}
	for my $value (multi_param('polarity')) {
		push @polarities, Untaint($value);
	}
	for my $value (multi_param('transitivity')) {
		push @transitivities, Untaint($value);
	}
	for my $value (multi_param('s_person')) {
		push @s_persons, Untaint($value);
	}
	for my $value (multi_param('s_number')) {
		push @s_numbers, Untaint($value);
	}
	for my $value (multi_param('s_gender')) {
		push @s_genders, Untaint($value);
	}
	for my $value (multi_param('o_person')) {
		push @o_persons, Untaint($value);
	}
	for my $value (multi_param('o_number')) {
		push @o_numbers, Untaint($value);
	}
	for my $value (multi_param('o_gender')) {
		push @o_genders, Untaint($value);
	}
	$root = forceValue('root', 'hou');
	$prefixedRoot = Untaint(decode_utf8(scalar param('prefixedRoot')));
	$gloss = forceValue('gloss', 'eat');
	$hasObject = Untaint(decode_utf8(scalar param('hasObject'))) eq 'yes';
	$Debug = 1;
} # init

sub solve {
	my $pfmTheory = "/tmp/pfm$$";
	open THEORY, "$pfmDir/garifuna.1.pfm"
		or die("Cannot read $pfmDir/garifuna.1.pfm");
	binmode THEORY, ":utf8";
	$/ = undef; # slurp
	my $theory = <THEORY>;
	close THEORY;
	$theory =~ s/ParadigmSchema/% ParadigmSchema/g;
	$theory =~ s/Lexeme:/% Lexeme:/g;
	$theory =~ s/^Stem/% Stem/mg;
	my $WORD = uc($gloss);
	my @toAdd = ("");
	push @toAdd, "notInteractive";
	push @toAdd, "Lexeme: $WORD";
	push @toAdd, "Meaning: $gloss";
	push @toAdd, "Syntactic category: V";
	push @toAdd, "Inflection class: " . ($hasObject ? 't' : 'i');
	push @toAdd, "Stem($WORD) = $root";
	if (length($prefixedRoot)) {
		push @toAdd, "Stem(<$WORD, S:{prefixed}>) = $prefixedRoot";
	}
	push @toAdd, "ParadigmSchema(V-" . ($hasObject ? 't' : 'i') . ") = {";
	my $transitivities = join(' ', @transitivities);
	my @schemaEntries;
	push @schemaEntries, join('/', @tenses) . " transitive " .
		join('/', @polarities) . " " .
		"AGR(SUBJ):{" .
			join('/', @s_numbers) . " " .join('/', @s_persons) . " " .
			join('/', @s_genders) . "}" . " " .
		"AGR(OBJ):{" .
			join('/', @o_numbers) . " " . join('/', @o_persons) . " " .
			join('/', @o_genders) . "}" .
		")" if $hasObject and $transitivities =~ /\btransitive\b/; 
	push @schemaEntries, "(" . join('/', @tenses) . " intransitive " .
		join('/', @polarities) . " " .
		"AGR(SUBJ):{" .
			join('/', @s_numbers) . " " . join('/', @s_persons) . " " .
			join('/', @s_genders) .
		"})"
		if $transitivities =~ /\bintransitive\b/; 
	$theory .= join("\n", @toAdd) . join("/\n", @schemaEntries) . "}\n";
	open THEORY, ">$pfmTheory" or die("Cannot write $pfmTheory");
	binmode THEORY, ":utf8";
	print THEORY $theory;
	close THEORY;
	my $runFile = "/tmp/runPFM";
	open RUN, ">$runFile" or die("cannot write $runFile");
	print RUN "immediateFile=$pfmTheory\n";
	close RUN;
	system("$parseProgram < $runFile");
	unlink ($pfmTheory, $runFile);
} # solve

init();
solve();

